import React from 'react';
import { Box, Text } from 'ink';
import type { GameState } from '../game/types';
import { WORLD_COUNT } from '../game/levels';

export const LevelClearScreen: React.FC<{ state: GameState }> = ({ state }) => {
  const remaining = WORLD_COUNT - state.levelIndex - 1;
  return (
    <Box flexDirection="column" alignItems="center" marginTop={6}>
      <Text bold color="green">
        WORLD {state.levelIndex + 1} CLEARED!
      </Text>
      <Text> </Text>
      {remaining > 0 ? (
        <>
          <Text>Loading next world...</Text>
          <Text dimColor>({remaining} remaining)</Text>
        </>
      ) : (
        <Text dimColor>Finishing up...</Text>
      )}
      <Text> </Text>
      <Text dimColor>Press Enter to continue</Text>
    </Box>
  );
};
