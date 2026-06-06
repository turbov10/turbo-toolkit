import React from 'react';
import { Box, Text } from 'ink';
import type { GameState } from '../game/types';
import { WORLD_COUNT } from '../game/levels';

export const LevelIntro: React.FC<{ state: GameState }> = ({ state }) => (
  <Box flexDirection="column" alignItems="center" marginTop={6}>
    <Text bold color="cyan">
      WORLD {state.levelIndex + 1} / {WORLD_COUNT}
    </Text>
    <Text> </Text>
    <Text>LIVES: {state.lives}</Text>
    <Text> </Text>
    <Text bold color="yellow">GET READY!</Text>
  </Box>
);
