import React from 'react';
import { Box, Text } from 'ink';

const W = 60;
const border = (inner: string): string[] => {
  const top = '+' + '='.repeat(W - 2) + '+';
  const mid = '|' + inner.padEnd(W - 2, ' ') + '|';
  const bot = '+' + '='.repeat(W - 2) + '+';
  return [top, mid, bot];
};

export const StartScreen: React.FC = () => {
  const title = 'TERMINAL PIXEL ADVENTURE';
  const titleLine = border(title)[1];
  const top = border('')[0];
  const bot = border('')[2];

  return (
    <Box flexDirection="column" alignItems="center" marginTop={2}>
      <Text color="green">{top}</Text>
      <Text color="green" bold>{titleLine}</Text>
      <Text color="green">{bot}</Text>
      <Text> </Text>
      <Text>A tiny terminal platform game inspired by classic side-scrollers.</Text>
      <Text> </Text>
      <Text>Controls:</Text>
      <Text>{'  <- / ->    Move'}</Text>
      <Text>{'  Space      Jump'}</Text>
      <Text>{'  Enter      Start / Confirm / Skip'}</Text>
      <Text>{'  P          Pause'}</Text>
      <Text>{'  M          Toggle audio (on pause screen)'}</Text>
      <Text>{'  Q          Quit'}</Text>
      <Text>{'  R          Restart (on game over / win)'}</Text>
      <Text> </Text>
      <Text color="yellow">Press Enter to Start</Text>
    </Box>
  );
};
