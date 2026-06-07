// Render a GameState into a structured color frame that the React/Ink layer
// can paint efficiently. We collapse adjacent same-color runs into "spans"
// so we don't create one <Text> node per character.
//
// Frame shape: VIEW_HEIGHT rows. Each row is a list of { text, color? } spans
// concatenated to form the visible line.

import type { GameState } from './types';
import { GAME_VIEW_HEIGHT, VIEW_HEIGHT, VIEW_WIDTH } from './constants';
import { WORLD_COUNT } from './levels';

export type ColorSpan = { text: string; color?: string };
export type ColorLine = ColorSpan[];
export type ColorFrame = ColorLine[];

type Cell = { ch: string; color?: string };

/** Collapse a ColorFrame into plain `string[]` (one string per row).
 *  Useful for callers that want a spec-compliant plain-text frame
 *  (e.g. for logging, tests, or a non-Ink renderer). */
export function frameToLines(frame: ColorFrame): string[] {
  return frame.map((line) =>
    line.map((span) => span.text).join(''),
  );
}

// Default per-tile colors. Ground ('#' at y >= groundTop) is overridden
// to brown in `tileColor()` below.
const DEFAULT_TILE_COLOR: Record<string, string | undefined> = {
  '#': 'gray',          // floating platforms (ground overrides to brown)
  'B': 'yellow',
  '?': 'green',
  'o': 'yellowBright',
  '~': 'cyan',
  'F': 'greenBright',
};

/** Brown for the 5-row ground. Saddle brown is a dark, earthy color that
 *  reads as "dirt" in a terminal and contrasts well with the cyan player
 *  and yellow coins. */
const GROUND_COLOR = '#8B4513';

const PLAYER_COLOR = 'cyanBright';
const ENEMY_COLOR = 'redBright';

/** Per-tile color, with the special case that '#' at or below the ground
 *  top is drawn brown instead of gray. */
function tileColor(tile: string, mapY: number, groundTop: number): string | undefined {
  if (tile === '#' && mapY >= groundTop) return GROUND_COLOR;
  return DEFAULT_TILE_COLOR[tile];
}

// ---------------------------------------------------------------------------
// HUD
// ---------------------------------------------------------------------------

function buildHud(state: GameState): ColorLine {
  const world = `WORLD ${state.levelIndex + 1}/${WORLD_COUNT}`;
  const lives = `LIVES: ${state.lives}`;
  const deaths = `DEATHS: ${state.deaths}`;

  // Top line: status.
  const status = `${world}    ${lives}    ${deaths}`;
  const statusPadded =
    status.length >= VIEW_WIDTH
      ? status.slice(0, VIEW_WIDTH)
      : status.padEnd(VIEW_WIDTH, ' ');

  return [
    { text: statusPadded, color: 'white' },
  ];
}

function buildHintLine(state: GameState): ColorLine {
  // Second HUD line: controls hint during PLAYING, otherwise blank.
  let text = '';
  if (state.status === 'PLAYING') {
    const audioTag = state.audio ? '' : ' (MUTED)';
    text = `<- -> move   SPACE jump   P pause   Q quit${audioTag}`;
  }
  const padded = text.length >= VIEW_WIDTH
    ? text.slice(0, VIEW_WIDTH)
    : text.padEnd(VIEW_WIDTH, ' ');
  return [{ text: padded, color: 'gray' }];
}

// ---------------------------------------------------------------------------
// Frame assembly
// ---------------------------------------------------------------------------

/** Paint a 2x2 sprite (player or enemy) into the buffer. The sprite char
 *  and color are the same for all four cells. Cells outside the viewport
 *  are clipped. */
function paintSprite(
  buffer: Cell[][],
  originX: number,
  originY: number,
  sizeX: number,
  sizeY: number,
  camX: number,
  camY: number,
  ch: string,
  color: string,
): void {
  for (let dy = 0; dy < sizeY; dy++) {
    for (let dx = 0; dx < sizeX; dx++) {
      const sx = Math.floor(originX) - camX + dx;
      const sy = Math.floor(originY) - camY + dy;
      if (sx >= 0 && sx < VIEW_WIDTH && sy >= 0 && sy < GAME_VIEW_HEIGHT) {
        buffer[sy][sx] = { ch, color };
      }
    }
  }
}

function buildBuffer(state: GameState): Cell[][] {
  const buffer: Cell[][] = [];
  for (let y = 0; y < GAME_VIEW_HEIGHT; y++) {
    buffer.push(new Array<Cell>(VIEW_WIDTH).fill({ ch: ' ' }));
  }

  const camX = Math.floor(state.camera.x);
  const camY = Math.floor(state.camera.y);
  const groundTop = state.level.groundTop;

  // Map tiles.
  for (let y = 0; y < GAME_VIEW_HEIGHT; y++) {
    const mapY = camY + y;
    if (mapY < 0 || mapY >= state.level.height) continue;
    const row = state.level.tiles[mapY];
    if (!row) continue;
    for (let x = 0; x < VIEW_WIDTH; x++) {
      const mapX = camX + x;
      if (mapX < 0 || mapX >= state.level.width) continue;
      const tile = row[mapX];
      buffer[y][x] = {
        ch: tile === '.' ? ' ' : tile,
        color: tileColor(tile, mapY, groundTop),
      };
    }
  }

  // Enemies — 2x2 sprite.
  for (const enemy of state.enemies) {
    paintSprite(buffer, enemy.x, enemy.y, enemy.width, enemy.height, camX, camY, 'g', ENEMY_COLOR);
  }

  // Player — 2x2 sprite.
  paintSprite(buffer, state.player.x, state.player.y, state.player.width, state.player.height, camX, camY, '@', PLAYER_COLOR);

  return buffer;
}

function collapseRow(row: Cell[]): ColorLine {
  const spans: ColorLine = [];
  let i = 0;
  while (i < row.length) {
    const c = row[i];
    let j = i + 1;
    while (j < row.length && row[j].color === c.color) {
      j++;
    }
    spans.push({ text: row.slice(i, j).map((r) => r.ch).join(''), color: c.color });
    i = j;
  }
  return spans;
}

export function renderFrame(state: GameState): ColorFrame {
  const buffer = buildBuffer(state);
  const lines: ColorFrame = [];

  lines.push(buildHud(state));
  lines.push(buildHintLine(state));

  for (const row of buffer) {
    // Pad to VIEW_WIDTH in case the camera exposed out-of-bounds cells.
    while (row.length < VIEW_WIDTH) row.push({ ch: ' ' });
    lines.push(collapseRow(row));
  }

  // Safety: ensure we always return exactly VIEW_HEIGHT lines.
  while (lines.length < VIEW_HEIGHT) {
    lines.push([{ text: ''.padEnd(VIEW_WIDTH, ' '), color: undefined }]);
  }
  if (lines.length > VIEW_HEIGHT) lines.length = VIEW_HEIGHT;
  return lines;
}

/** Spec-compliant convenience: render a frame and return it as plain
 *  `string[]` (one string per row, no color information). */
export function renderFrameLines(state: GameState): string[] {
  return frameToLines(renderFrame(state));
}
