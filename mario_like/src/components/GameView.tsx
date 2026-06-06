import React from 'react';
import { Box, Text } from 'ink';
import type { GameState } from '../game/types';
import { renderFrame, type ColorLine } from '../game/renderer';

const FrameLine: React.FC<{ line: ColorLine }> = ({ line }) => (
  <>
    {line.map((span, i) =>
      span.color ? (
        <Text key={i} color={span.color}>{span.text}</Text>
      ) : (
        <Text key={i}>{span.text}</Text>
      ),
    )}
  </>
);

export const GameView: React.FC<{ state: GameState }> = ({ state }) => {
  const frame = renderFrame(state);
  return (
    <Box flexDirection="column">
      {frame.map((line, y) => (
        <Text key={y}>
          <FrameLine line={line} />
        </Text>
      ))}
    </Box>
  );
};
