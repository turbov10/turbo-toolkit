// Collision helpers. All coordinates are in tile units (floats allowed).

import type { Level } from './types';
import { SOLID_TILE_CHARS } from './constants';

export function isSolidChar(ch: string | undefined): boolean {
  if (!ch) return false;
  return SOLID_TILE_CHARS.has(ch);
}

export function getTileAt(level: Level, x: number, y: number): string {
  if (x < 0 || x >= level.width || y < 0 || y >= level.height) {
    return '.';
  }
  return level.tiles[y][x] ?? '.';
}

export function isSolidAt(level: Level, x: number, y: number): boolean {
  return isSolidChar(getTileAt(level, x, y));
}

/** True if the AABBs overlap. Inputs may be float. */
export function aabbOverlap(
  a: { x: number; y: number; width: number; height: number },
  b: { x: number; y: number; width: number; height: number },
): boolean {
  return (
    a.x < b.x + b.width &&
    a.x + a.width > b.x &&
    a.y < b.y + b.height &&
    a.y + a.height > b.y
  );
}

/**
 * Check if an AABB placed at (x, y) with the given size would overlap any
 * solid tile in the level. We sample every tile the AABB covers.
 *
 * The -0.0001 fudge on the bottom/right edge means a player whose right or
 * bottom edge sits exactly on a tile boundary does NOT count as overlapping
 * that tile. This is what lets axis-separated movement work cleanly.
 */
export function collidesWithSolid(
  x: number,
  y: number,
  width: number,
  height: number,
  level: Level,
): boolean {
  const x1 = Math.floor(x);
  const y1 = Math.floor(y);
  const x2 = Math.floor(x + width - 0.0001);
  const y2 = Math.floor(y + height - 0.0001);
  for (let ty = y1; ty <= y2; ty++) {
    for (let tx = x1; tx <= x2; tx++) {
      if (isSolidAt(level, tx, ty)) return true;
    }
  }
  return false;
}
