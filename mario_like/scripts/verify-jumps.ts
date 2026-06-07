// Verification script: for each elevated platform, check whether the player
// (now 2x2) can reach it by jumping from the ground or from another platform.
// Checks position at every frame (player may land and walk off before dying).

import { RAW_MAPS, GROUND_THICKNESS, parseLevel } from '../src/game/levels.js';
import {
  MOVE_SPEED,
  GRAVITY,
  JUMP_VELOCITY,
  MAX_FALL_SPEED,
} from '../src/game/constants.js';
import {
  isSolidAt,
  moveWithCollision,
} from '../src/game/collision.js';
import type { Player } from '../src/game/types.js';

type SimPlayer = Player;

const PLAYER_W = 2;
const PLAYER_H = 2;

function makeSimPlayer(x: number, y: number): SimPlayer {
  return { x, y, vx: 0, vy: 0, width: PLAYER_W, height: PLAYER_H, facing: 'right', onGround: false };
}

const SOLID = new Set(['#', 'B', '?']);

/** Top of the ground (row index of the first solid ground row). */
function groundTopOf(level: ReturnType<typeof parseLevel>): number {
  return level.height - GROUND_THICKNESS;
}

/** Player's y (top) when standing on a surface whose top edge is at `topEdgeY`. */
function standYFor(topEdgeY: number): number {
  return topEdgeY - PLAYER_H;
}

function tryLandOn(
  level: ReturnType<typeof parseLevel>,
  startX: number,
  startY: number,
  facingRight: boolean,
  target: PlatformInfo,
  maxFrames: number = 300,
): boolean {
  const standY = standYFor(target.y);
  const p = makeSimPlayer(startX, startY);
  p.onGround = true;
  p.vy = JUMP_VELOCITY;
  p.onGround = false;
  p.vx = facingRight ? MOVE_SPEED : -MOVE_SPEED;

  for (let f = 0; f < maxFrames; f++) {
    p.vy += GRAVITY;
    if (p.vy > MAX_FALL_SPEED) p.vy = MAX_FALL_SPEED;
    moveWithCollision(p, level);
    if (p.y >= level.height) return false;
    if (
      p.onGround &&
      Math.abs(p.y - standY) < 0.1 &&
      // 2x2 player: its right edge is at p.x + 2, so the landing x range
      // extends a tile further than the 1x1 case.
      p.x + PLAYER_W >= target.minX &&
      p.x <= target.maxX + 1
    ) {
      return true;
    }
  }
  return false;
}

type PlatformInfo = { id: string; minX: number; maxX: number; y: number; ch: string };

/** Find all elevated platform groups (contiguous runs of solid tiles on the
 *  same row, not on the ground).
 *
 *  Multi-row platforms are 2 tiles thick for visual depth, but the player
 *  can only land on the TOP row. We skip sub-rows here so the verifier
 *  doesn't try to "land" on a row that's already covered by the row above. */
function findPlatforms(level: ReturnType<typeof parseLevel>): PlatformInfo[] {
  const groundTop = groundTopOf(level);
  const platforms: PlatformInfo[] = [];
  for (let y = 0; y < groundTop; y++) {
    let i = 0;
    while (i < level.width) {
      const ch = level.tiles[y][i];
      if (!ch || !SOLID.has(ch)) { i++; continue; }
      const start = i;
      while (i < level.width && level.tiles[y][i] === ch) i++;
      const end = i - 1;

      // Sub-row detection: if every cell in this run is also solid on the
      // row above (with the same char), this is the 2nd+ row of a multi-row
      // platform and the player can never land here directly.
      if (y > 0) {
        let isSubRow = true;
        for (let x = start; x <= end; x++) {
          if (level.tiles[y - 1][x] !== ch) {
            isSubRow = false;
            break;
          }
        }
        if (isSubRow) continue;
      }

      platforms.push({
        id: `(${start}-${end},${y}) ${ch}`,
        minX: start,
        maxX: end,
        y,
        ch,
      });
    }
  }
  return platforms;
}

function verifyLevel(raw: string[], label: string): void {
  const level = parseLevel(raw);
  console.log(`--- ${label} (${level.width}x${level.height}) ---`);
  const platforms = findPlatforms(level);
  const groundTop = groundTopOf(level);
  const unreachable: PlatformInfo[] = [];

  for (const target of platforms) {
    let foundLaunch: string | null = null;

    // Try launching from the ground at every tile within 35 horizontal tiles.
    // Player (2x2) stands with bottom on the top edge of the ground, so
    // launchStandY = groundTop - PLAYER_H.
    const launchStandY = standYFor(groundTop);
    for (let launchX = Math.max(0, target.minX - 35); launchX <= Math.min(level.width - 1, target.maxX + 35); launchX++) {
      if (level.tiles[groundTop][launchX] !== '#') continue;
      if (!isSolidAt(level, launchX, launchStandY + PLAYER_H)) continue;

      for (const facingRight of [true, false]) {
        if (tryLandOn(level, launchX, launchStandY, facingRight, target)) {
          foundLaunch = `ground@${launchX}${facingRight ? '→' : '←'}`;
          break;
        }
      }
      if (foundLaunch) break;
    }

    // Try launching from every other platform's top edge.
    if (!foundLaunch) {
      for (const source of platforms) {
        if (source === target) continue;
        if (Math.abs(source.minX - target.minX) > 35) continue;
        const sourceStandY = standYFor(source.y);
        for (const launchX of [source.minX, source.maxX, Math.floor((source.minX + source.maxX) / 2)]) {
          if (!isSolidAt(level, launchX, sourceStandY + PLAYER_H)) continue;
          for (const facingRight of [true, false]) {
            if (tryLandOn(level, launchX, sourceStandY, facingRight, target)) {
              foundLaunch = `${source.id}@${launchX}${facingRight ? '→' : '←'}`;
              break;
            }
          }
          if (foundLaunch) break;
        }
        if (foundLaunch) break;
      }
    }

    if (!foundLaunch) {
      unreachable.push(target);
    } else {
      console.log(`  OK  ${target.id}  via ${foundLaunch}`);
    }
  }

  if (unreachable.length === 0) {
    console.log(`\nAll ${platforms.length} platforms reachable.\n`);
  } else {
    console.log(`\nFAIL: ${unreachable.length}/${platforms.length} platforms unreachable:`);
    for (const p of unreachable) {
      console.log(`  ${p.id}`);
    }
    console.log();
  }
}

console.log('=== Jump Verification ===\n');
verifyLevel(RAW_MAPS[0], 'World 1');
verifyLevel(RAW_MAPS[1], 'World 2');
