import React from 'react';
import { Box, Text } from 'ink';
import type { GameState } from '../game/types';
import { WORLD_COUNT } from '../game/levels';

export const GameWinScreen: React.FC<{ state: GameState }> = ({ state }) => (
  <Box flexDirection="column" alignItems="center" marginTop={4}>
    <Text bold color="green">
      CONGRATULATIONS!
    </Text>
    <Text> </Text>
    <Text>You cleared all worlds.</Text>
    <Text> </Text>
    <Text>Stats:</Text>
    <Text>{`  Worlds cleared: ${state.clearedLevels + 1} / ${WORLD_COUNT}`}</Text>
    <Text>{`  Lives remaining: ${state.lives}`}</Text>
    <Text>{`  Deaths: ${state.deaths}`}</Text>
    <Text> </Text>
    <Text color="yellow">Press R to Play Again</Text>
    <Text>Press Q to Quit</Text>
  </Box>
);
