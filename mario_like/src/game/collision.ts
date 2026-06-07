// Collision helpers. All coordinates are in tile units (floats allowed).
//
// The high-level flow is:
//   1. `isSolidTile` / `isSolidAt` / `getTileAt` — tile-level queries.
//   2. `collidesWithSolid` — query: would an AABB at (x, y) overlap a solid?
//   3. `moveWithCollision` — action: actually move an entity by its velocity
//      (or an explicit override) and snap to solid edges. Returns whether
//      each axis was blocked and whether the entity landed on something.
//   4. `checkPlayerEnemyCollision` / `checkPlayerGoalCollision` /
//      `checkFallDeath` — game-rule queries used by the state machine.

import type { Enemy, Level, Player } from './types';
import { SOLID_TILE_CHARS } from './constants';

// ---------------------------------------------------------------------------
// Tile-level queries
// ---------------------------------------------------------------------------

/** True if a single tile character is solid (blocks movement). */
export function isSolidTile(ch: string | undefined): boolean {
  if (!ch) return false;
  return SOLID_TILE_CHARS.has(ch);
}

/** Return the character at tile (x, y) or '.' if out of bounds. */
export function getTileAt(level: Level, x: number, y: number): string {
  if (x < 0 || x >= level.width || y < 0 || y >= level.height) {
    return '.';
  }
  return level.tiles[y][x] ?? '.';
}

/** True if the tile at (x, y) is solid. */
export function isSolidAt(level: Level, x: number, y: number): boolean {
  return isSolidTile(getTileAt(level, x, y));
}

// ---------------------------------------------------------------------------
// AABB queries
// ---------------------------------------------------------------------------

/** True if two axis-aligned bounding boxes overlap. Inputs may be float. */
export function checkAabbCollision(
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
 * True if an AABB placed at (x, y) with the given size would overlap any
 * solid tile in the level. We sample every tile the AABB covers.
 *
 * The -0.0001 fudge on the bottom/right edge means an AABB whose right or
 * bottom edge sits exactly on a tile boundary does NOT count as overlapping
 * that tile. This is what lets axis-separated movement work cleanly: when
 * the player is standing on a tile, their bottom edge touches the tile's
 * top edge but they don't count as "inside" it.
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

// ---------------------------------------------------------------------------
// Movement with collision
// ---------------------------------------------------------------------------

/** Anything that can be moved by `moveWithCollision`. `onGround` is optional
 *  and only updated on entities that carry it (i.e. the player). */
export type Movable = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  width: number;
  height: number;
  onGround?: boolean;
};

/** Result of a `moveWithCollision` call. */
export type CollisionResult = {
  /** True if horizontal movement was blocked by a solid. */
  blockedX: boolean;
  /** True if vertical movement was blocked by a solid. */
  blockedY: boolean;
  /** True if the entity landed on top of a solid (vy was downward). */
  landed: boolean;
};

/**
 * Find the first solid tile the AABB at (x, y, w, h) overlaps. Used by
 * `moveWithCollision` to figure out exactly which tile we hit so we can
 * snap to its edge correctly even when the entity moves more than one tile
 * in a single frame.
 */
function findSolidTile(
  level: Level,
  x: number,
  y: number,
  w: number,
  h: number,
): { tx: number; ty: number } | null {
  const x1 = Math.floor(x);
  const y1 = Math.floor(y);
  const x2 = Math.floor(x + w - 0.0001);
  const y2 = Math.floor(y + h - 0.0001);
  for (let ty = y1; ty <= y2; ty++) {
    for (let tx = x1; tx <= x2; tx++) {
      if (isSolidAt(level, tx, ty)) return { tx, ty };
    }
  }
  return null;
}

/**
 * Move `entity` by its velocity (or by explicit `dx`/`dy` if provided) and
 * snap to any solid tile it would overlap. Horizontal and vertical are
 * resolved independently so a corner approach never locks the entity.
 *
 * Snap logic:
 *   - Horizontal: if a wall is hit, align the entity's edge to the wall's
 *     near edge. The entity can never end the frame inside a wall.
 *   - Vertical (falling): if a floor is hit, align the entity's bottom
 *     edge to the top of the floor tile and mark `onGround = true`.
 *   - Vertical (rising): if a ceiling is hit, align the entity's top
 *     edge to the bottom of the ceiling tile.
 *
 * Edge clamping to the level bounds happens first.
 */
export function moveWithCollision(
  entity: Movable,
  level: Level,
  dx?: number,
  dy?: number,
): CollisionResult {
  const moveX = dx ?? entity.vx;
  const moveY = dy ?? entity.vy;
  const result: CollisionResult = { blockedX: false, blockedY: false, landed: false };

  // --- Horizontal ---
  if (moveX !== 0) {
    let newX = entity.x + moveX;

    // Clamp to the level bounds so the entity can't walk off either end.
    if (newX < 0) {
      entity.x = 0;
      result.blockedX = true;
    } else if (newX + entity.width > level.width) {
      entity.x = level.width - entity.width;
      result.blockedX = true;
    } else if (collidesWithSolid(newX, entity.y, entity.width, entity.height, level)) {
      const tile = findSolidTile(level, newX, entity.y, entity.width, entity.height);
      if (tile) {
        if (moveX > 0) {
          // Moving right: align our right edge to the tile's left edge.
          entity.x = tile.tx - entity.width;
        } else {
          // Moving left: align our left edge to the tile's right edge.
          entity.x = tile.tx + 1;
        }
      }
      result.blockedX = true;
    } else {
      entity.x = newX;
    }
  }

  // --- Vertical ---
  if (moveY !== 0) {
    const newY = entity.y + moveY;

    // Sweep check: the endpoint collidesWithSolid is not enough because a
    // fast-falling entity (vy up to MAX_FALL_SPEED = 1.8) can cross an
    // entire 1-tile-thick platform in a single frame without the endpoint
    // check noticing. Instead, scan every integer tile row between the
    // start and end y and use the first solid one we find.
    const dir = moveY > 0 ? 1 : -1;
    const yStart = Math.floor(entity.y + (moveY > 0 ? entity.height - 0.0001 : 0));
    const yEnd = Math.floor(newY + (moveY > 0 ? entity.height - 0.0001 : 0));
    let hitTileY = -1;
    for (let ty = yStart + dir; ; ty += dir) {
      if (dir > 0 ? ty > yEnd : ty < yEnd) break;
      if (isSolidAt(level, Math.floor(entity.x), ty)) {
        hitTileY = ty;
        break;
      }
    }

    if (hitTileY >= 0) {
      if (moveY > 0) {
        // Falling: place the entity on top of the tile we landed on.
        entity.y = hitTileY - entity.height;
        if (entity.onGround !== undefined) entity.onGround = true;
        result.landed = true;
      } else {
        // Rising: place the entity just below the tile we bonked.
        entity.y = hitTileY + entity.height;
      }
      result.blockedY = true;
    } else {
      entity.y = newY;
      // We were falling (vy > 0) and didn't hit anything: we're airborne.
      if (entity.onGround !== undefined && moveY > 0) {
        entity.onGround = false;
      }
    }
  }

  return result;
}

// ---------------------------------------------------------------------------
// Game-rule queries
// ---------------------------------------------------------------------------

/** True if the player overlaps any enemy. */
export function checkPlayerEnemyCollision(player: Player, enemies: Enemy[]): boolean {
  for (const enemy of enemies) {
    if (checkAabbCollision(player, enemy)) return true;
  }
  return false;
}

/** True if the player overlaps the goal cell. */
export function checkPlayerGoalCollision(
  player: Player,
  goal: { x: number; y: number },
): boolean {
  return checkAabbCollision(player, { x: goal.x, y: goal.y, width: 1, height: 1 });
}

/** True if the player has fallen past the bottom of the level. */
export function checkFallDeath(player: { y: number }, level: Level): boolean {
  return player.y >= level.height;
}
