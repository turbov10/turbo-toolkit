// Pre-rendered ASCII art for the game's title screen and decorative clouds.
//
// All generated once at module load time using `figlet` so the React
// components just drop in the resulting strings.

import figlet from 'figlet';

// ---------------------------------------------------------------------------
// Title logo
// ---------------------------------------------------------------------------

export const GAME_TITLE = 'ASCII MARIO';

/** Big "ASCII MARIO" rendered in ANSI Shadow box-drawing characters.
 *  Matches the visual language of similar terminal tools (Deep Code CLI). */
export const TITLE_LOGO: string = figlet.textSync(GAME_TITLE, {
  font: 'ANSI Shadow',
  width: 100,
  whitespaceBreak: true,
});

// ---------------------------------------------------------------------------
// Cloud mask (figlet-generated)
// ---------------------------------------------------------------------------

/**
 * Cloud decorative shape. We feed "oOo" to figlet in ANSI Shadow, which
 * produces three decorative "o" glyphs (each ~8 cols wide, 6 rows tall) made
 * of box-drawing characters. We then take just the first "o" and use it as
 * a MASK: for every non-space position in the mask we place a `~` tile in
 * the level. The renderer draws `~` tiles in cyan, so the cloud appears as
 * a decorative cyan puffy shape.
 *
 * The mask is about 8 cols wide and 6 rows tall. Each cloud in the level is
 * placed at a top-left (x, y) and stamped from this mask.
 */
const CLOUD_FIGLET: string = figlet.textSync('oOo', {
  font: 'ANSI Shadow',
  width: 40,
  whitespaceBreak: true,
});

function extractFigletMask(
  text: string,
  maxDx: number,
  maxDy: number,
): Array<{ dx: number; dy: number }> {
  const lines = text.split('\n');
  const tiles: Array<{ dx: number; dy: number }> = [];
  for (let y = 0; y < lines.length && y < maxDy; y++) {
    const line = lines[y] ?? '';
    for (let x = 0; x < line.length && x < maxDx; x++) {
      if (line[x] !== ' ') tiles.push({ dx: x, dy: y });
    }
  }
  return tiles;
}

/** The first "o" from the figlet "oOo" output — 8 cols x 6 rows. */
export const CLOUD_TILES: ReadonlyArray<{ dx: number; dy: number }> =
  extractFigletMask(CLOUD_FIGLET, 8, 6);
