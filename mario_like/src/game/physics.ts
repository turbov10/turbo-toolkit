// Physics: per-frame updates for the player, enemies, and the camera.
// Designed to be called once per game tick from `gameState.updateGameState`.
//
// All collision resolution lives in `collision.ts`; this module just composes
// the high-level steps.

import type { Camera, Enemy, Level, Player } from './types';
import { collidesWithSolid, isSolidAt, moveWithCollision } from './collision';
import {
  ENEMY_SPEED,
  GRAVITY,
  JUMP_VELOCITY,
  MAX_FALL_SPEED,
  MOVE_SPEED,
  VIEW_WIDTH,
} from './constants';

// ---------------------------------------------------------------------------
// Player
// ---------------------------------------------------------------------------

/**
 * Translate the held/pressed input into velocities. Pure velocity update —
 * no movement is applied here. Called once per frame from `updatePlayer`.
 */
export function applyInputToPlayer(
  player: Player,
  left: boolean,
  right: boolean,
  jumpPressed: boolean,
): void {
  // Horizontal: if exactly one direction is held, walk that way; otherwise stop.
  if (left && !right) {
    player.vx = -MOVE_SPEED;
    player.facing = 'left';
  } else if (right && !left) {
    player.vx = MOVE_SPEED;
    player.facing = 'right';
  } else {
    player.vx = 0;
  }

  // Jump only if standing on ground. No double jump, no air control on jump.
  if (jumpPressed && player.onGround) {
    player.vy = JUMP_VELOCITY;
    player.onGround = false;
  }
}

/** Apply gravity acceleration and clamp to terminal velocity. */
export function applyGravity(player: Player): void {
  player.vy += GRAVITY;
  if (player.vy > MAX_FALL_SPEED) {
    player.vy = MAX_FALL_SPEED;
  }
}

/** Move the player with collision resolution. Thin wrapper for symmetry. */
export function movePlayerWithCollision(player: Player, level: Level): void {
  moveWithCollision(player, level);
}

/**
 * Top-level per-frame player update. Order matters:
 *   1. Read input → set vx, possibly trigger jump (sets vy)
 *   2. Apply gravity to vy
 *   3. Move with collision (resolves solid overlaps axis-by-axis)
 */
export function updatePlayer(
  player: Player,
  level: Level,
  left: boolean,
  right: boolean,
  jumpPressed: boolean,
): void {
  applyInputToPlayer(player, left, right, jumpPressed);
  applyGravity(player);
  movePlayerWithCollision(player, level);
}

// ---------------------------------------------------------------------------
// Enemies
// ---------------------------------------------------------------------------

/**
 * Step every enemy one frame. Mushrooms walk left/right, turn around at walls,
 * and turn around at platform edges so they don't walk off cliffs.
 *
 * Enemies are not moved via `moveWithCollision` because they only ever travel
 * horizontally (vy is always 0). Instead we do a forward query: would the
 * enemy collide if placed at `newX`? If yes, turn around; if no, commit the
 * move. This keeps the wall response snappy and avoids needing to handle
 * `onGround` on enemies.
 */
export function updateEnemies(enemies: Enemy[], level: Level): void {
  for (const enemy of enemies) {
    const newX = enemy.x + enemy.vx;

    // 1) Wall in front? Query only — do not move yet.
    if (collidesWithSolid(newX, enemy.y, enemy.width, enemy.height, level)) {
      enemy.direction = (enemy.direction * -1) as -1 | 1;
      enemy.vx = ENEMY_SPEED * enemy.direction;
      continue;
    }

    // 2) Platform edge in front? Check the tile directly under the front foot.
    //    If there's no ground there, the enemy would walk off a cliff, so we
    //    turn around before stepping.
    const frontX = enemy.direction > 0 ? enemy.x + enemy.width : enemy.x;
    const belowY = enemy.y + enemy.height;
    if (!isSolidAt(level, Math.floor(frontX), Math.floor(belowY))) {
      enemy.direction = (enemy.direction * -1) as -1 | 1;
      enemy.vx = ENEMY_SPEED * enemy.direction;
      continue;
    }

    // 3) Clear path — walk.
    enemy.x = newX;
  }
}

// ---------------------------------------------------------------------------
// Camera
// ---------------------------------------------------------------------------

/**
 * Keep the player roughly centered horizontally, clamped so the camera never
 * goes past either edge of the level. Vertical camera is always 0 because
 * the level is exactly as tall as the game view.
 */
export function updateCamera(camera: Camera, player: Player, level: Level): void {
  const playerCenter = player.x + player.width / 2;
  const desired = playerCenter - VIEW_WIDTH / 2;
  const maxX = Math.max(0, level.width - VIEW_WIDTH);
  camera.x = Math.max(0, Math.min(desired, maxX));
  camera.y = 0;
}
