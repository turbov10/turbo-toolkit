import React from 'react';
import { Box, Text } from 'ink';

export const GameOverScreen: React.FC = () => (
  <Box flexDirection="column" alignItems="center" marginTop={6}>
    <Text bold color="red">
      GAME OVER
    </Text>
    <Text> </Text>
    <Text>Press R to Restart</Text>
    <Text>Press Q to Quit</Text>
  </Box>
);
