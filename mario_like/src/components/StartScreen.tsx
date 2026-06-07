import React from 'react';
import { Box, Text } from 'ink';
import { TITLE_LOGO } from '../ascii-art';

// A small mini-scene shown on the start screen as a visual preview of
// the in-game rendering. Uses the same character set and color scheme as
// the renderer so the player recognizes what they're about to play.
function MiniScene(): React.ReactElement {
  return (
    <Box flexDirection="column" alignItems="center">
      <Text>
        <Text color="cyan">~</Text>
        <Text>{'        '}</Text>
        <Text color="cyan">~</Text>
        <Text>{'              '}</Text>
        <Text color="cyan">~</Text>
      </Text>
      <Text>
        <Text>{'        '}</Text>
        <Text color="green">????</Text>
        <Text>{'       '}</Text>
        <Text color="yellow">B</Text>
        <Text>{'           '}</Text>
        <Text color="yellow">o</Text>
      </Text>
      <Text>
        <Text color="gray">####</Text>
        <Text>{'    '}</Text>
        <Text color="cyanBright">@</Text>
        <Text>{'  '}</Text>
        <Text color="redBright">g</Text>
        <Text>{'    '}</Text>
        <Text color="gray">######</Text>
        <Text>{'    '}</Text>
        <Text color="greenBright">F</Text>
      </Text>
    </Box>
  );
}

const CONTROLS: ReadonlyArray<[string, string]> = [
  ['<- / ->',  'Move'],
  ['Space',    'Jump'],
  ['Enter',    'Start / Confirm / Skip'],
  ['P',        'Pause'],
  ['M',        'Toggle audio (on pause screen)'],
  ['Q',        'Quit'],
  ['R',        'Restart (on game over / win)'],
];

export const StartScreen: React.FC = () => (
  <Box flexDirection="column" alignItems="center" marginY={1}>
    {/* Big ASCII-art title in a rounded panel. The pre-rendered logo from
        ascii-art.ts is dropped in verbatim — every line is its own Text
        child so we get reliable left-alignment of the box-drawing glyphs. */}
    <Box
      borderStyle="round"
      borderColor="green"
      paddingX={2}
      flexDirection="column"
      alignItems="center"
    >
      {TITLE_LOGO.split('\n').map((line, i) => (
        <Text key={i} color="green">{line || ' '}</Text>
      ))}
    </Box>

    {/* Subtitle — one-line tagline below the logo. */}
    <Box marginTop={1}>
      <Text dimColor>A tiny terminal platform game</Text>
    </Box>

    {/* Mini scene preview so the player sees what they're about to play. */}
    <Box marginY={1}>
      <MiniScene />
    </Box>

    {/* Controls panel — rounded border, cyan to match the player's color. */}
    <Box
      borderStyle="round"
      borderColor="cyan"
      paddingX={2}
      flexDirection="column"
    >
      <Text bold color="cyan">{'Controls'}</Text>
      {CONTROLS.map(([key, desc]) => (
        <Text key={key}>{`  ${key.padEnd(10, ' ')}  ${desc}`}</Text>
      ))}
    </Box>

    {/* Start prompt — yellow, bold, with a prompt-style caret. */}
    <Box marginTop={1}>
      <Text color="yellow" bold>{'> Press Enter to Start'}</Text>
    </Box>
  </Box>
);
