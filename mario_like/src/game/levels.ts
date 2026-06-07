// Built-in worlds. Each world is built by `createRawLevel` from a small
// declarative config, and the result is a `string[]` tile grid (one string
// per row). `parseLevel` then strips 'P' / 'G' markers into metadata.
//
// The procedural config is just a more readable way to author the same
// `string[]` the spec asks for. If you prefer to edit raw grids, every
// map is also exported as a finished `string[]` (see the `RAW_MAPS` export).
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
//   ~  background cloud (no collision; shape comes from figlet mask)
//
// All maps are 22 rows tall. The ground occupies the bottom 5 rows
// (y=17..21) and the renderer colors it brown. Player is 2x2 and stands
// at y=15 (bottom at y=17). Floating platforms are 2 rows thick.

import { CLOUD_TILES } from '../ascii-art';
import type { Level, Tile } from './types';

type Gap = { start: number; end: number };
type Platform = { x: number; y: number; tiles: string };
type Cloud = { x: number; y: number };
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

/** How many rows of ground the renderer should color brown. */
export const GROUND_THICKNESS = 5;

/** Every elevated platform is this many rows thick. */
export const PLATFORM_THICKNESS = 2;

function createRawLevel(config: LevelConfig): string[] {
  const { width, height, groundY, groundGaps, platforms, clouds, coins, playerStart, enemies, goal } = config;

  // Start with all air.
  const grid: string[][] = [];
  for (let y = 0; y < height; y++) {
    grid.push(new Array<string>(width).fill('.'));
  }

  // Ground: GROUND_THICKNESS rows thick, with gaps.
  for (let dy = 0; dy < GROUND_THICKNESS; dy++) {
    const y = groundY - dy;
    if (y < 0) break;
    for (let x = 0; x < width; x++) {
      const inGap = groundGaps.some((g) => x >= g.start && x < g.end);
      grid[y][x] = inGap ? '.' : '#';
    }
  }

  // Elevated platforms: PLATFORM_THICKNESS rows thick.
  for (const p of platforms) {
    for (let dy = 0; dy < PLATFORM_THICKNESS; dy++) {
      const y = p.y + dy;
      if (y < 0 || y >= height) continue;
      for (let i = 0; i < p.tiles.length; i++) {
        const x = p.x + i;
        if (x >= 0 && x < width) {
          grid[y][x] = p.tiles[i];
        }
      }
    }
  }

  // Decorative clouds: stamp the figlet-generated mask at each cloud
  // origin. Each `~` is rendered in cyan.
  for (const c of clouds) {
    for (const tile of CLOUD_TILES) {
      const x = c.x + tile.dx;
      const y = c.y + tile.dy;
      if (x >= 0 && x < width && y >= 0 && y < height) {
        grid[y][x] = '~';
      }
    }
  }

  // Decorative coins (no collision, no collection).
  for (const coin of coins) {
    if (coin.x >= 0 && coin.x < width && coin.y >= 0 && coin.y < height) {
      grid[coin.y][coin.x] = 'o';
    }
  }

  // Player spawn (2x2).
  grid[playerStart.y][playerStart.x] = 'P';

  // Enemy spawns (2x2).
  for (const e of enemies) {
    grid[e.y][e.x] = 'G';
  }

  // Goal flag stays as a static tile.
  grid[goal.y][goal.x] = 'F';

  return grid.map((row) => row.join(''));
}

// -----------------------------------------------------------------------------
// World 1 — tutorial. 160 tiles wide, 2 small gaps, 2 mushrooms.
//   gap 1: 4 tiles at x=30..33
//   gap 2: 5 tiles at x=80..84
//   question blocks above gap 1, brick step above gap 2, high platform bridge
// Player (2x2) stands at y=15, bottom at y=17 (ground top).
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
    { x: 44, y: 13, tiles: '?????' },      // question blocks over the first gap (y=13-14)
    { x: 92, y: 11, tiles: 'BBBBB' },      // brick step over the second gap (y=11-12)
    { x: 105, y: 9, tiles: '######' },     // high platform reachable from the bricks (y=9-10)
  ],
  clouds: [
    { x: 10, y: 0 },
    { x: 40, y: 1 },
    { x: 75, y: 0 },
    { x: 110, y: 1 },
    { x: 145, y: 0 },
  ],
  coins: [
    { x: 48, y: 10 },
    { x: 108, y: 6 },
    { x: 140, y: 13 },
  ],
  playerStart: { x: 5, y: 15 },
  enemies: [
    { x: 60, y: 15 },
    { x: 130, y: 15 },
  ],
  goal: { x: 152, y: 15 },
});

// -----------------------------------------------------------------------------
// World 2 — busier. 220 tiles wide, 4 gaps, 4 mushrooms, multi-tier platforms.
// -----------------------------------------------------------------------------
const MAP2_RAW: string[] = createRawLevel({
  width: 220,
  height: 22,
  groundY: 21,
  groundGaps: [
    { start: 25, end: 29 },   // gap 1
    { start: 60, end: 65 },   // gap 2
    { start: 100, end: 106 }, // gap 3
    { start: 150, end: 155 }, // gap 4
  ],
  platforms: [
    { x: 35, y: 13, tiles: 'BBBBBB' },     // brick step after gap 1
    { x: 50, y: 10, tiles: '########' },   // mid-air platform
    { x: 70, y: 13, tiles: '????' },       // question blocks
    { x: 85, y: 8, tiles: '##########' },  // high hard platform
    { x: 110, y: 13, tiles: 'BBBBBB' },    // brick step after gap 3
    { x: 125, y: 11, tiles: '##########' }, // mid-air platform (reachable from bricks and ground)
    { x: 160, y: 13, tiles: '????' },      // question blocks
    { x: 180, y: 9, tiles: '########' },   // final high platform
  ],
  clouds: [
    { x: 8, y: 0 },
    { x: 30, y: 1 },
    { x: 55, y: 0 },
    { x: 80, y: 1 },
    { x: 115, y: 0 },
    { x: 140, y: 1 },
    { x: 170, y: 0 },
    { x: 200, y: 1 },
  ],
  coins: [
    { x: 38, y: 10 },
    { x: 55, y: 7 },
    { x: 90, y: 5 },
    { x: 115, y: 10 },
    { x: 165, y: 10 },
  ],
  playerStart: { x: 5, y: 15 },
  enemies: [
    { x: 45, y: 15 },
    { x: 90, y: 15 },
    { x: 140, y: 15 },
    { x: 195, y: 15 },
  ],
  goal: { x: 215, y: 15 },
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
    groundTop: height - GROUND_THICKNESS,
  };
}

/** Convenience: get the parsed level for an index. */
export function getLevel(index: number): Level {
  const raw = RAW_MAPS[index] ?? RAW_MAPS[0];
  return parseLevel(raw);
}

// Re-export the Tile type for convenience.
export type { Tile };
