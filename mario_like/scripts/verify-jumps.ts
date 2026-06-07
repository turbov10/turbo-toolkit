// Verification script: for each elevated platform, check whether the player
// can reach it by jumping from the ground or from another platform.
// Checks position at every frame (player may land and walk off before dying).

import { RAW_MAPS, parseLevel } from '../src/game/levels.js';
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

function makeSimPlayer(x: number, y: number): SimPlayer {
  return { x, y, vx: 0, vy: 0, width: 1, height: 1, facing: 'right', onGround: false };
}

const SOLID = new Set(['#', 'B', '?']);

function simulateJump(
  level: ReturnType<typeof parseLevel>,
  startX: number,
  startY: number,
  facingRight: boolean,
  maxFrames: number = 300,
): { everLanded: boolean; finalX: number; finalY: number; died: boolean } {
  const p = makeSimPlayer(startX, startY);
  p.onGround = true;
  p.vy = JUMP_VELOCITY;
  p.onGround = false;
  p.vx = facingRight ? MOVE_SPEED : -MOVE_SPEED;

  let died = false;
  let everLanded = false;
  for (let f = 0; f < maxFrames; f++) {
    p.vy += GRAVITY;
    if (p.vy > MAX_FALL_SPEED) p.vy = MAX_FALL_SPEED;
    moveWithCollision(p, level);
    if (p.y >= level.height) {
      died = true;
      break;
    }
  }
  return { everLanded, finalX: p.x, finalY: p.y, died };
}

type PlatformInfo = { id: string; minX: number; maxX: number; y: number; ch: string };

function findPlatforms(level: ReturnType<typeof parseLevel>): PlatformInfo[] {
  const groundY = level.height - 1;
  const platforms: PlatformInfo[] = [];
  for (let y = 0; y < groundY; y++) {
    let i = 0;
    while (i < level.width) {
      const ch = level.tiles[y][i];
      if (!ch || !SOLID.has(ch)) { i++; continue; }
      const start = i;
      while (i < level.width && level.tiles[y][i] === ch) i++;
      const end = i - 1;
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
  const groundY = level.height - 1;
  const unreachable: PlatformInfo[] = [];

  for (const target of platforms) {
    const standY = target.y - 1;
    let foundLaunch: string | null = null;

    // Try launching from the ground at every tile within 35 horizontal tiles.
    for (let launchX = Math.max(0, target.minX - 35); launchX <= Math.min(level.width - 1, target.maxX + 35); launchX++) {
      if (level.tiles[groundY][launchX] !== '#') continue;
      const launchStandY = groundY - 1;
      if (!isSolidAt(level, launchX, launchStandY + 1)) continue;

      for (const facingRight of [true, false]) {
        const p = makeSimPlayer(launchX, launchStandY);
        p.onGround = true;
        p.vy = JUMP_VELOCITY;
        p.onGround = false;
        p.vx = facingRight ? MOVE_SPEED : -MOVE_SPEED;

        let landed = false;
        for (let f = 0; f < 300; f++) {
          p.vy += GRAVITY;
          if (p.vy > MAX_FALL_SPEED) p.vy = MAX_FALL_SPEED;
          moveWithCollision(p, level);
          if (p.y >= level.height) break;
          if (
            p.onGround &&
            Math.abs(p.y - standY) < 0.1 &&
            p.x >= target.minX - 0.5 &&
            p.x <= target.maxX + 0.5
          ) {
            landed = true;
            break;
          }
        }

        if (landed) {
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
        const sourceStandY = source.y - 1;
        for (const launchX of [source.minX, source.maxX, Math.floor((source.minX + source.maxX) / 2)]) {
          if (!isSolidAt(level, launchX, sourceStandY + 1)) continue;
          for (const facingRight of [true, false]) {
            const p = makeSimPlayer(launchX, sourceStandY);
            p.onGround = true;
            p.vy = JUMP_VELOCITY;
            p.onGround = false;
            p.vx = facingRight ? MOVE_SPEED : -MOVE_SPEED;

            let landed = false;
            for (let f = 0; f < 300; f++) {
              p.vy += GRAVITY;
              if (p.vy > MAX_FALL_SPEED) p.vy = MAX_FALL_SPEED;
              moveWithCollision(p, level);
              if (p.y >= level.height) break;
              if (
                p.onGround &&
                Math.abs(p.y - standY) < 0.1 &&
                p.x >= target.minX - 0.5 &&
                p.x <= target.maxX + 0.5
              ) {
                landed = true;
                break;
              }
            }

            if (landed) {
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
