// Built-in worlds. Each world is built by `createRawLevel` from a small
// declarative config, and the result is a `string[]` tile grid (one string
// per row). `parseLevel` then strips 'P' / 'G' markers into metadata.
//
// The procedural config is just a more readable way to author the same
// `string[]` the spec asks for. If you prefer to edit raw grids, every map
// is also exported as a finished `string[]` (see the `RAW_MAPS` export).
//
// Tile characters used in the source:
//   .  air (rendered as space)
//   #  solid ground / platform
//   B  solid brick
//   ?  solid question / decoration block
//   P  player spawn (removed from the static grid, kept in metadata)
//   G  enemy spawn  (removed from the static grid, kept in metadata)
//   F  goal flag    (kept in the static grid)
//   o  decorative coin (no collision, no collection)
//   ~  background cloud (no collision)
//
// All maps are 22 rows tall. The ground lives on row 21 (the last row).
// The visible game area is 22 rows (HUD is drawn separately on top).

import type { Level, Tile } from './types';

type Gap = { start: number; end: number };
type Platform = { x: number; y: number; tiles: string };
type Cloud = { x: number; y: number; width: number };
type Coin = { x: number; y: number };
type EnemyPos = { x: number; y: number };

type LevelConfig = {
  width: number;
  height: number;
  groundY: number;
  groundGaps: Gap[];
  platforms: Platform[];
  clouds: Cloud[];
  coins: Coin[];
  playerStart: { x: number; y: number };
  enemies: EnemyPos[];
  goal: { x: number; y: number };
};

function createRawLevel(config: LevelConfig): string[] {
  const { width, height, groundY, groundGaps, platforms, clouds, coins, playerStart, enemies, goal } = config;

  // Start with all air.
  const grid: string[][] = [];
  for (let y = 0; y < height; y++) {
    grid.push(new Array<string>(width).fill('.'));
  }

  // Ground row, with gaps.
  for (let x = 0; x < width; x++) {
    const inGap = groundGaps.some((g) => x >= g.start && x < g.end);
    grid[groundY][x] = inGap ? '.' : '#';
  }

  // Elevated platforms (bricks, question blocks, hard platforms).
  for (const p of platforms) {
    for (let i = 0; i < p.tiles.length; i++) {
      const x = p.x + i;
      if (x >= 0 && x < width) {
        grid[p.y][x] = p.tiles[i];
      }
    }
  }

  // Decorative clouds in the sky.
  for (const c of clouds) {
    for (let x = c.x; x < c.x + c.width; x++) {
      if (x >= 0 && x < width && c.y >= 0 && c.y < height) {
        grid[c.y][x] = '~';
      }
    }
  }

  // Decorative coins (no collision, no collection).
  for (const coin of coins) {
    if (coin.x >= 0 && coin.x < width && coin.y >= 0 && coin.y < height) {
      grid[coin.y][coin.x] = 'o';
    }
  }

  // Player spawn.
  grid[playerStart.y][playerStart.x] = 'P';

  // Enemy spawns.
  for (const e of enemies) {
    grid[e.y][e.x] = 'G';
  }

  // Goal flag stays as a static tile.
  grid[goal.y][goal.x] = 'F';

  return grid.map((row) => row.join(''));
}

// -----------------------------------------------------------------------------
// World 1 — tutorial. 160 tiles wide, 2 small gaps, 2 mushrooms, easy jumps.
//   gap 1: 4 tiles at x=30..33
//   gap 2: 5 tiles at x=80..84
//   question blocks above gap 1, brick step above gap 2, high platform bridge
// -----------------------------------------------------------------------------
const MAP1_RAW: string[] = createRawLevel({
  width: 160,
  height: 22,
  groundY: 21,
  groundGaps: [
    { start: 30, end: 34 },
    { start: 80, end: 85 },
  ],
  platforms: [
    { x: 44, y: 17, tiles: '?????' },      // question blocks over the first gap
    { x: 92, y: 15, tiles: 'BBBBB' },      // brick step over the second gap
    { x: 105, y: 13, tiles: '######' },    // high platform reachable from the bricks
  ],
  clouds: [
    { x: 10, y: 1, width: 3 },
    { x: 40, y: 2, width: 3 },
    { x: 75, y: 1, width: 3 },
    { x: 110, y: 2, width: 3 },
    { x: 135, y: 1, width: 3 },
  ],
  coins: [
    { x: 48, y: 14 },
    { x: 108, y: 10 },
    { x: 140, y: 17 },
  ],
  playerStart: { x: 5, y: 20 },
  enemies: [
    { x: 60, y: 20 },
    { x: 130, y: 20 },
  ],
  goal: { x: 152, y: 20 },
});

// -----------------------------------------------------------------------------
// World 2 — busier. 220 tiles wide, 4 gaps, 4 mushrooms, multi-tier platforms.
// -----------------------------------------------------------------------------
const MAP2_RAW: string[] = createRawLevel({
  width: 220,
  height: 22,
  groundY: 21,
  groundGaps: [
    { start: 25, end: 29 },   // 4-tile gap
    { start: 60, end: 65 },   // 5-tile gap
    { start: 100, end: 106 }, // 6-tile gap
    { start: 150, end: 155 }, // 5-tile gap
  ],
  platforms: [
    { x: 35, y: 17, tiles: 'BBBBBB' },     // brick step after gap 1
    { x: 50, y: 14, tiles: '########' },   // mid-air platform
    { x: 70, y: 17, tiles: '????' },       // question block reward
    { x: 85, y: 12, tiles: '##########' }, // high hard platform
    { x: 110, y: 17, tiles: 'BBBBBB' },    // brick step after gap 3
    { x: 125, y: 15, tiles: '##########' }, // mid-air platform (reachable from bricks and ground)
    { x: 160, y: 17, tiles: '????' },      // question blocks
    { x: 180, y: 13, tiles: '########' },  // final high platform
  ],
  clouds: [
    { x: 8, y: 1, width: 3 },
    { x: 30, y: 2, width: 3 },
    { x: 55, y: 1, width: 3 },
    { x: 80, y: 2, width: 3 },
    { x: 115, y: 1, width: 3 },
    { x: 140, y: 2, width: 3 },
    { x: 170, y: 1, width: 3 },
    { x: 200, y: 2, width: 3 },
  ],
  coins: [
    { x: 38, y: 14 },
    { x: 55, y: 11 },
    { x: 90, y: 9 },
    { x: 115, y: 14 },
    { x: 165, y: 14 },
  ],
  playerStart: { x: 5, y: 20 },
  enemies: [
    { x: 45, y: 20 },
    { x: 90, y: 20 },
    { x: 140, y: 20 },
    { x: 195, y: 20 },
  ],
  goal: { x: 215, y: 20 },
});

// -----------------------------------------------------------------------------
// Public exports
// -----------------------------------------------------------------------------

/** All raw tile grids, in play order. Each entry is `Level.height` strings
 *  of `Level.width` characters. */
export const RAW_MAPS: string[][] = [MAP1_RAW, MAP2_RAW];

/** Number of built-in worlds. */
export const WORLD_COUNT = RAW_MAPS.length;

/**
 * Turn a raw tile grid (where 'P' and 'G' are special markers) into a Level
 * with those markers removed from the static grid and stored in metadata.
 * 'F' stays in the static grid so the renderer can draw the flag.
 */
export function parseLevel(rawTiles: string[]): Level {
  const height = rawTiles.length;
  const width = rawTiles[0]?.length ?? 0;

  const tiles: string[][] = [];
  let playerStart = { x: 0, y: 0 };
  const enemyStarts: { x: number; y: number }[] = [];
  let goal = { x: 0, y: 0 };
  let goalFound = false;

  for (let y = 0; y < height; y++) {
    const row: string[] = [];
    for (let x = 0; x < width; x++) {
      const ch = rawTiles[y][x];
      if (ch === 'P') {
        playerStart = { x, y };
        row.push('.');
      } else if (ch === 'G') {
        enemyStarts.push({ x, y });
        row.push('.');
      } else if (ch === 'F') {
        goal = { x, y };
        goalFound = true;
        row.push('F');
      } else {
        row.push(ch);
      }
    }
    tiles.push(row);
  }

  if (!goalFound) {
    // Place a default goal at the far right of the ground row.
    goal = { x: width - 2, y: height - 2 };
    tiles[goal.y][goal.x] = 'F';
  }

  return {
    width,
    height,
    tiles: tiles.map((r) => r.join('')),
    playerStart,
    enemyStarts,
    goal,
  };
}

/** Convenience: get the parsed level for an index. */
export function getLevel(index: number): Level {
  const raw = RAW_MAPS[index] ?? RAW_MAPS[0];
  return parseLevel(raw);
}

// Re-export the Tile type for convenience.
export type { Tile };
