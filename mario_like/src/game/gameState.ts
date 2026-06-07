// Pure state-machine logic. App.tsx owns the state and calls `updateGameState`
// once per tick.
//
// Quit is intentionally NOT handled here — App.tsx watches for Q globally and
// calls Ink's `useApp().exit()`. That keeps the state machine free of side
// effects beyond optional audio (BEL).

import type { Enemy, GameState, InputState, Level, Player } from './types';
import { WORLD_COUNT, getLevel } from './levels';
import {
  DEFAULT_AUDIO,
  ENEMY_SPEED,
  INITIAL_LIVES,
  LEVEL_CLEAR_DURATION_MS,
  LEVEL_INTRO_DURATION_MS,
  PLAYER_DEAD_DURATION_MS,
} from './constants';
import {
  checkFallDeath,
  checkPlayerEnemyCollision,
  checkPlayerGoalCollision,
} from './collision';
import {
  updateCamera,
  updateEnemies,
  updatePlayer,
} from './physics';

// ---------------------------------------------------------------------------
// Audio helper
// ---------------------------------------------------------------------------

/** Emit a terminal bell (BEL) if audio is enabled. No-op otherwise. */
function beep(audio: boolean): void {
  if (!audio) return;
  process.stdout.write('\x07');
}

// ---------------------------------------------------------------------------
// Construction
// ---------------------------------------------------------------------------

/** Build a fresh Player at the level's spawn point, with zero velocity.
 *  The player is a 2x2 tile sprite. */
function makePlayer(level: Level): Player {
  return {
    x: level.playerStart.x,
    y: level.playerStart.y,
    vx: 0,
    vy: 0,
    width: 2,
    height: 2,
    facing: 'right',
    onGround: false,
  };
}

/** Build a fresh array of Enemies from the level's spawn markers.
 *  Mushroom enemies are also 2x2 tile sprites. */
function makeEnemies(level: Level, levelIndex: number): Enemy[] {
  return level.enemyStarts.map((e, i) => ({
    id: `enemy-${levelIndex}-${i}`,
    type: 'mushroom',
    x: e.x,
    y: e.y,
    vx: ENEMY_SPEED,
    direction: -1,
    width: 2,
    height: 2,
  }));
}

/** Build the initial GameState at the title screen, World 1, full lives. */
export function resetGame(): GameState {
  const level = getLevel(0);
  return {
    status: 'START_SCREEN',
    levelIndex: 0,
    lives: INITIAL_LIVES,
    deaths: 0,
    clearedLevels: 0,
    player: makePlayer(level),
    enemies: makeEnemies(level, 0),
    camera: { x: 0, y: 0 },
    level,
    statusStartTime: 0,
    audio: DEFAULT_AUDIO,
  };
}

/** Reset player / enemies / camera to the start of the current level. */
export function resetCurrentLevel(state: GameState): GameState {
  const level = getLevel(state.levelIndex);
  return {
    ...state,
    player: makePlayer(level),
    enemies: makeEnemies(level, state.levelIndex),
    camera: { x: 0, y: 0 },
    level,
  };
}

/** Advance to the next world, or transition to GAME_WIN if this was the last. */
function goToNextLevel(state: GameState, now: number): GameState {
  const nextIndex = state.levelIndex + 1;
  if (nextIndex >= WORLD_COUNT) {
    beep(state.audio);
    return {
      ...state,
      status: 'GAME_WIN',
      statusStartTime: now,
    };
  }
  const base: GameState = {
    ...state,
    levelIndex: nextIndex,
    clearedLevels: state.clearedLevels + 1,
    status: 'LEVEL_INTRO',
    statusStartTime: now,
  };
  return resetCurrentLevel(base);
}

// ---------------------------------------------------------------------------
// Per-state transitions
// ---------------------------------------------------------------------------

/** Title screen: Enter starts the game. */
function handleStartScreen(state: GameState, input: InputState, now: number): GameState {
  if (input.enterPressed) {
    const base: GameState = {
      ...state,
      status: 'LEVEL_INTRO',
      statusStartTime: now,
    };
    return resetCurrentLevel(base);
  }
  return state;
}

/** Auto-advance after the intro timer. */
function handleLevelIntro(state: GameState, now: number): GameState {
  if (now - state.statusStartTime >= LEVEL_INTRO_DURATION_MS) {
    return { ...state, status: 'PLAYING', statusStartTime: now };
  }
  return state;
}

/** The main game loop tick: input → physics → collisions → state changes. */
function handlePlaying(state: GameState, input: InputState, now: number): GameState {
  if (input.pausePressed) {
    return { ...state, status: 'PAUSED', statusStartTime: now };
  }

  // --- Step the simulation ---
  const player = { ...state.player };
  const enemies = state.enemies.map((e) => ({ ...e }));
  const camera = { ...state.camera };
  const level = state.level;

  // Beep on a successful jump (input was consumed and the player was on
  // the ground when the jump was applied).
  const wasOnGround = player.onGround;
  updatePlayer(player, level, input.left, input.right, input.jumpPressed);
  if (input.jumpPressed && wasOnGround) beep(state.audio);

  updateEnemies(enemies, level);
  updateCamera(camera, player, level);

  // --- Death / clear checks (order matters: enemy before goal before fall) ---

  if (checkPlayerEnemyCollision(player, enemies)) {
    beep(state.audio);
    return {
      ...state,
      status: 'PLAYER_DEAD',
      lives: state.lives - 1,
      deaths: state.deaths + 1,
      statusStartTime: now,
      player,
      enemies,
      camera,
    };
  }

  if (checkPlayerGoalCollision(player, level.goal)) {
    beep(state.audio);
    return {
      ...state,
      status: 'LEVEL_CLEAR',
      statusStartTime: now,
      player,
      enemies,
      camera,
    };
  }

  if (checkFallDeath(player, level)) {
    beep(state.audio);
    return {
      ...state,
      status: 'PLAYER_DEAD',
      lives: state.lives - 1,
      deaths: state.deaths + 1,
      statusStartTime: now,
      player,
      enemies,
      camera,
    };
  }

  return { ...state, player, enemies, camera };
}

/** Paused: P/Enter resume, M toggles audio. */
function handlePaused(state: GameState, input: InputState, now: number): GameState {
  if (input.pausePressed || input.enterPressed) {
    return { ...state, status: 'PLAYING', statusStartTime: now };
  }
  if (input.skipPressed) {
    // skipPressed == "M" in the pause screen → toggle audio.
    return { ...state, audio: !state.audio };
  }
  return state;
}

/** World clear: auto-advance after the timer, or skip on Enter. */
function handleLevelClear(state: GameState, input: InputState, now: number): GameState {
  const elapsed = now - state.statusStartTime;
  if (input.skipPressed || input.enterPressed || elapsed >= LEVEL_CLEAR_DURATION_MS) {
    return goToNextLevel(state, now);
  }
  return state;
}

/** Player death: respawn with intro, or transition to GAME_OVER if out of lives. */
function handlePlayerDead(state: GameState, input: InputState, now: number): GameState {
  const elapsed = now - state.statusStartTime;
  if (input.skipPressed || input.enterPressed || elapsed >= PLAYER_DEAD_DURATION_MS) {
    if (state.lives <= 0) {
      return { ...state, status: 'GAME_OVER', statusStartTime: now };
    }
    return resetCurrentLevel({ ...state, status: 'LEVEL_INTRO', statusStartTime: now });
  }
  return state;
}

/** Game over: R restarts the whole game. */
function handleGameOver(state: GameState, input: InputState): GameState {
  if (input.restartPressed) return resetGame();
  return state;
}

/** Game win: R restarts the whole game. */
function handleGameWin(state: GameState, input: InputState): GameState {
  if (input.restartPressed) return resetGame();
  return state;
}

// ---------------------------------------------------------------------------
// Public entry point
// ---------------------------------------------------------------------------

/** One tick of the state machine. Pure: (state, input, now) -> state. */
export function updateGameState(state: GameState, input: InputState, now: number): GameState {
  switch (state.status) {
    case 'START_SCREEN':
      return handleStartScreen(state, input, now);
    case 'LEVEL_INTRO':
      return handleLevelIntro(state, now);
    case 'PLAYING':
      return handlePlaying(state, input, now);
    case 'PAUSED':
      return handlePaused(state, input, now);
    case 'LEVEL_CLEAR':
      return handleLevelClear(state, input, now);
    case 'PLAYER_DEAD':
      return handlePlayerDead(state, input, now);
    case 'GAME_OVER':
      return handleGameOver(state, input);
    case 'GAME_WIN':
      return handleGameWin(state, input);
  }
}
