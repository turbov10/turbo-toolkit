import React from 'react';
import { Box, Text } from 'ink';
import type { GameState } from '../game/types';
import { WORLD_COUNT } from '../game/levels';
import { LEVEL_INTRO_DURATION_MS } from '../game/constants';

// Classic ASCII spinner that rotates every ~100ms. We use a single cell so
// the box width doesn't jitter as the frame changes.
const SPINNER = ['|', '/', '-', '\\'] as const;
const SPIN_INTERVAL_MS = 100;

/** Number of full lives to render as a visual row of stars beneath the
 *  numeric lives counter. Capped at INITIAL_LIVES (3) for layout stability. */
const MAX_LIVES = 3;

export const LevelIntro: React.FC<{ state: GameState }> = ({ state }) => {
  // The component re-renders every game tick (30 FPS), so reading Date.now()
  // here gives us a free-running countdown / spinner without any extra timers.
  const elapsed = Date.now() - state.statusStartTime;
  const remaining = Math.max(
    0,
    Math.ceil((LEVEL_INTRO_DURATION_MS - elapsed) / 1000),
  );
  const spinnerFrame =
    SPINNER[Math.floor(elapsed / SPIN_INTERVAL_MS) % SPINNER.length];

  const filledLives = Math.min(state.lives, MAX_LIVES);
  const emptyLives = Math.max(0, MAX_LIVES - filledLives);

  return (
    <Box flexDirection="column" alignItems="center" marginY={2}>
      {/* World number — rounded border, cyan to match the player. */}
      <Box
        borderStyle="round"
        borderColor="cyan"
        paddingX={3}
        flexDirection="column"
        alignItems="center"
      >
        <Text bold color="cyan">
          {`WORLD ${state.levelIndex + 1} / ${WORLD_COUNT}`}
        </Text>
      </Box>

      {/* Lives — number + visual row of stars. */}
      <Box marginY={1} flexDirection="column" alignItems="center">
        <Text>
          {'LIVES: '}
          <Text bold color="red">{state.lives}</Text>
        </Text>
        <Text color="red">{'*'.repeat(filledLives)}</Text>
        <Text dimColor>{'.'.repeat(emptyLives)}</Text>
      </Box>

      {/* Get ready — rounded border, yellow, with spinner + countdown. */}
      <Box borderStyle="round" borderColor="yellow" paddingX={2} marginTop={1}>
        <Text bold color="yellow">
          {`GET READY! ${spinnerFrame}  ${remaining}`}
        </Text>
      </Box>
    </Box>
  );
};
