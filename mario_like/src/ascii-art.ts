// Pre-rendered ASCII art for the game's title screen.
//
// Generated once at module load time using `figlet` so the text component
// just drops in the string. ANSI Shadow was chosen to match the visual
// language of similar terminal tools (e.g. Deep Code CLI's WelcomeScreen).
//
// To regenerate or change the font, run:
//   npx tsx scripts/preview-figlet.ts
// and copy the output below.

import figlet from 'figlet';

export const GAME_TITLE = 'ASCII MARIO';

export const TITLE_LOGO: string = figlet.textSync(GAME_TITLE, {
  font: 'ANSI Shadow',
  width: 100,
  whitespaceBreak: true,
});
