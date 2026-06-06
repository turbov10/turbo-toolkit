// Physics: per-frame updates for the player, enemies, and the camera.
// Designed to be called once per game tick from `gameState.updateGameState`.

import type { Camera, Enemy, Level, Player } from './types';
import { collidesWithSolid, isSolidAt } from './collision';
import {
  ENEMY_SPEED,
  GRAVITY,
  JUMP_VELOCITY,
  MAX_FALL_SPEED,
  MOVE_SPEED,
  VIEW_WIDTH,
} from './constants';

// -----------------------------------------------------------------------------
// Player
// -----------------------------------------------------------------------------

/** Translate the held/pressed input into velocities. */
export function applyInputToPlayer(
  player: Player,
  left: boolean,
  right: boolean,
  jumpPressed: boolean,
): void {
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

export function applyGravity(player: Player): void {
  player.vy += GRAVITY;
  if (player.vy > MAX_FALL_SPEED) {
    player.vy = MAX_FALL_SPEED;
  }
}

/**
 * Move the player by their current velocity, axis-by-axis, snapping to the
 * edge of any solid tile we hit. This guarantees the player can never end a
 * frame inside a wall.
 */
export function movePlayerWithCollision(player: Player, level: Level): void {
  // --- Horizontal ---
  if (player.vx !== 0) {
    let newX = player.x + player.vx;

    // Hard clamp to the level bounds so the player can't walk off either end.
    if (newX < 0) newX = 0;
    if (newX + player.width > level.width) newX = level.width - player.width;

    if (collidesWithSolid(newX, player.y, player.width, player.height, level)) {
      // Snap to the edge of the colliding tile.
      if (player.vx > 0) {
        // Moving right: align our right edge to the colliding tile's left edge.
        const rightEdge = player.x + player.width;
        player.x = Math.floor(rightEdge + player.vx) - player.width;
      } else {
        // Moving left: align our left edge to the colliding tile's right edge.
        player.x = Math.floor(newX) + 1;
      }
      player.vx = 0;
    } else {
      player.x = newX;
    }
  }

  // --- Vertical ---
  if (player.vy !== 0) {
    const newY = player.y + player.vy;

    if (collidesWithSolid(player.x, newY, player.width, player.height, level)) {
      if (player.vy > 0) {
        // Falling: snap to the top of the tile we landed on, mark on ground.
        const bottomEdge = player.y + player.height;
        player.y = Math.floor(bottomEdge + player.vy) - player.height;
        player.onGround = true;
      } else {
        // Rising: bonk on the underside of the tile.
        player.y = Math.floor(newY) + 1;
      }
      player.vy = 0;
    } else {
      player.y = newY;
      player.onGround = false;
    }
  }
}

// -----------------------------------------------------------------------------
// Enemies
// -----------------------------------------------------------------------------

/**
 * Step every enemy one frame. Mushrooms walk left/right, turn around at walls,
 * and turn around at platform edges so they don't walk off cliffs.
 */
export function updateEnemies(enemies: Enemy[], level: Level): void {
  for (const enemy of enemies) {
    const newX = enemy.x + enemy.vx;

    // 1) Wall in front?
    if (
      collidesWithSolid(newX, enemy.y, enemy.width, enemy.height, level)
    ) {
      enemy.direction = (enemy.direction * -1) as -1 | 1;
      enemy.vx = ENEMY_SPEED * enemy.direction;
      continue;
    }

    // 2) Platform edge in front? Check the tile directly under the front foot.
    const frontX =
      enemy.direction > 0 ? enemy.x + enemy.width : enemy.x;
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

// -----------------------------------------------------------------------------
// Camera
// -----------------------------------------------------------------------------

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
