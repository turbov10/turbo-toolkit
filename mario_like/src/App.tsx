import React, { useEffect, useRef, useState } from 'react';
import { Box, Text, useApp, useInput } from 'ink';
import { StartScreen } from './components/StartScreen';
import { LevelIntro } from './components/LevelIntro';
import { GameView } from './components/GameView';
import { PauseScreen } from './components/PauseScreen';
import { LevelClearScreen } from './components/LevelClearScreen';
import { PlayerDeadScreen } from './components/PlayerDeadScreen';
import { GameOverScreen } from './components/GameOverScreen';
import { GameWinScreen } from './components/GameWinScreen';
import { resetGame, updateGameState } from './game/gameState';
import type { GameState, InputState } from './game/types';
import {
  clearEdgeTriggers,
  createInitialInputState,
  resetInput,
} from './game/input';
import {
  INPUT_HOLD_TIMEOUT_MS,
  TICK_MS,
  VIEW_HEIGHT,
  VIEW_WIDTH,
} from './game/constants';

type TerminalSize = { columns: number; rows: number };

const App: React.FC = () => {
  const { exit } = useApp();
  const [state, setState] = useState<GameState>(() => resetGame());
  const [size, setSize] = useState<TerminalSize>(() => ({
    columns: process.stdout.columns ?? VIEW_WIDTH,
    rows: process.stdout.rows ?? VIEW_HEIGHT,
  }));

  const stateRef = useRef(state);
  stateRef.current = state;
  const prevStatusRef = useRef(state.status);

  const inputRef = useRef<InputState>(createInitialInputState());
  const leftTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rightTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Resize listener — only valid if stdout is a TTY.
  useEffect(() => {
    const onResize = () => {
      setSize({
        columns: process.stdout.columns ?? VIEW_WIDTH,
        rows: process.stdout.rows ?? VIEW_HEIGHT,
      });
    };
    process.stdout.on('resize', onResize);
    return () => {
      process.stdout.off('resize', onResize);
    };
  }, []);

  // Game loop.
  useEffect(() => {
    const id = setInterval(() => {
      const now = Date.now();
      const input = inputRef.current;
      setState((prev) => {
        const next = updateGameState(prev, input, now);
        // If the status changed, wipe any held keys / edge flags so a key
        // the player was holding at the moment of transition does not bleed
        // into the new state.
        if (next.status !== prev.status) {
          prevStatusRef.current = next.status;
          resetInput(input);
        }
        return next;
      });
      // Clear edge-triggered flags after they have been processed.
      clearEdgeTriggers(inputRef.current);
    }, TICK_MS);
    return () => clearInterval(id);
  }, []);

  // Clean up hold timers on unmount.
  useEffect(() => {
    return () => {
      if (leftTimer.current) clearTimeout(leftTimer.current);
      if (rightTimer.current) clearTimeout(rightTimer.current);
    };
  }, []);

  // Keyboard input.
  useInput((input, key) => {
    const is = inputRef.current;

    // --- Global quit (Q) — handled here, not in the state machine. ---
    if (input === 'q' || input === 'Q') {
      exit();
      return;
    }

    // --- Held keys (left / right) with timeout-based release detection. ---
    if (key.leftArrow) {
      is.left = true;
      if (leftTimer.current) clearTimeout(leftTimer.current);
      leftTimer.current = setTimeout(() => {
        is.left = false;
      }, INPUT_HOLD_TIMEOUT_MS);
    }
    if (key.rightArrow) {
      is.right = true;
      if (rightTimer.current) clearTimeout(rightTimer.current);
      rightTimer.current = setTimeout(() => {
        is.right = false;
      }, INPUT_HOLD_TIMEOUT_MS);
    }

    // --- Edge-triggered keys. ---
    if (key.return) {
      is.enterPressed = true;
      is.skipPressed = true; // Enter also advances overlays.
    }
    if (input === ' ') is.jumpPressed = true;
    if (input === 'p' || input === 'P') is.pausePressed = true;
    if (input === 'm' || input === 'M') is.skipPressed = true; // M = mute toggle on pause screen
    if (input === 'r' || input === 'R') is.restartPressed = true;
  });

  // Terminal too small.
  if (size.columns < VIEW_WIDTH || size.rows < VIEW_HEIGHT) {
    return (
      <Box paddingX={1} paddingY={1} flexDirection="column">
        <Text color="red">
          Terminal too small ({size.columns}x{size.rows}).
        </Text>
        <Text>
          Please resize your terminal to at least {VIEW_WIDTH}x{VIEW_HEIGHT}.
        </Text>
      </Box>
    );
  }

  const s = state;
  switch (s.status) {
    case 'START_SCREEN':
      return <StartScreen />;
    case 'LEVEL_INTRO':
      return <LevelIntro state={s} />;
    case 'PLAYING':
      return <GameView state={s} />;
    case 'PAUSED':
      return <PauseScreen state={s} />;
    case 'LEVEL_CLEAR':
      return <LevelClearScreen state={s} />;
    case 'PLAYER_DEAD':
      return <PlayerDeadScreen state={s} />;
    case 'GAME_OVER':
      return <GameOverScreen />;
    case 'GAME_WIN':
      return <GameWinScreen state={s} />;
  }
};

export default App;
