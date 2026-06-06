import React from 'react';
import { Box, Text } from 'ink';
import type { GameState } from '../game/types';

export const PauseScreen: React.FC<{ state: GameState }> = ({ state }) => (
  <Box flexDirection="column" alignItems="center" marginTop={6}>
    <Text bold color="yellow">
      PAUSED
    </Text>
    <Text> </Text>
    <Text>Press P or Enter to Resume</Text>
    <Text>Press M to Toggle Audio ({state.audio ? 'on' : 'off'})</Text>
    <Text>Press Q to Quit</Text>
  </Box>
);
