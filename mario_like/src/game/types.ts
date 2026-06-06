// All shared types for the game.

// A single tile character. Stored as plain string in the level grid for
// ergonomics, but constrained to this set.
export type Tile =
  | '.' // air
  | '#' // solid ground
  | 'B' // solid brick
  | '?' // solid question / decoration block
  | 'F' // goal flag
  | 'o' // decorative coin
  | '~' // background cloud
  | 'P' // player spawn (stripped from static grid by parseLevel)
  | 'G'; // enemy spawn  (stripped from static grid by parseLevel)

export type GameStatus =
  | 'START_SCREEN'
  | 'LEVEL_INTRO'
  | 'PLAYING'
  | 'PAUSED'
  | 'LEVEL_CLEAR'
  | 'PLAYER_DEAD'
  | 'GAME_OVER'
  | 'GAME_WIN';

export type Player = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  width: number;
  height: number;
  facing: 'left' | 'right';
  onGround: boolean;
};

export type Enemy = {
  id: string;
  type: 'mushroom';
  x: number;
  y: number;
  vx: number;
  direction: -1 | 1;
  width: number;
  height: number;
};

// A level is a fixed-size grid of single-character tiles.
// tiles[y][x] gives the character at column x, row y.
export type Level = {
  width: number;
  height: number;
  tiles: string[];
  playerStart: { x: number; y: number };
  enemyStarts: { x: number; y: number }[];
  goal: { x: number; y: number };
};

export type Camera = {
  x: number;
  y: number;
};

// Live input state. `left`/`right` are level-triggered (held).
// The `*Pressed` flags are edge-triggered and cleared after one game tick.
export type InputState = {
  left: boolean;
  right: boolean;
  jumpPressed: boolean;
  pausePressed: boolean;
  enterPressed: boolean;
  skipPressed: boolean;   // generic "advance past this overlay" edge flag
  restartPressed: boolean;
  quitPressed: boolean;
};

export type GameState = {
  status: GameStatus;
  levelIndex: number;
  lives: number;
  deaths: number;
  clearedLevels: number;
  player: Player;
  enemies: Enemy[];
  camera: Camera;
  level: Level;
  statusStartTime: number;
  audio: boolean;          // toggleable via a key in Pause screen
};
