import React from 'react';
import { Box, Text } from 'ink';
import type { GameState } from '../game/types';
import { WORLD_COUNT } from '../game/levels';

export const PlayerDeadScreen: React.FC<{ state: GameState }> = ({ state }) => {
  const next = state.lives <= 0 ? 'GAME OVER' : `World ${state.levelIndex + 1}`;
  return (
    <Box flexDirection="column" alignItems="center" marginTop={6}>
      <Text bold color="red">
        OUCH!
      </Text>
      <Text> </Text>
      <Text>Lives left: {state.lives}</Text>
      <Text> </Text>
      {state.lives > 0 ? (
        <Text>Restarting {next} / {WORLD_COUNT}...</Text>
      ) : (
        <Text>No lives left.</Text>
      )}
      <Text> </Text>
      <Text dimColor>Press Enter to continue</Text>
    </Box>
  );
};
