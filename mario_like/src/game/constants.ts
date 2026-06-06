// Game constants. All physics values are per-frame at FPS=30.

// ---------------------------------------------------------------------------
// Timing
// ---------------------------------------------------------------------------
export const FPS = 30;
export const TICK_MS = 1000 / FPS;

// ---------------------------------------------------------------------------
// Viewport (in tile characters)
// ---------------------------------------------------------------------------
export const VIEW_WIDTH = 80;
export const VIEW_HEIGHT = 24;

// Top of the view is reserved for the HUD (1 line: status / 1 line: hint).
export const HUD_ROWS = 2;
export const GAME_VIEW_HEIGHT = VIEW_HEIGHT - HUD_ROWS;

// ---------------------------------------------------------------------------
// Physics (per-frame at FPS)
// ---------------------------------------------------------------------------
export const MOVE_SPEED = 0.45;       // tiles per frame
export const GRAVITY = 0.12;          // tiles per frame^2
export const JUMP_VELOCITY = -1.8;    // tiles per frame (negative = up)
export const MAX_FALL_SPEED = 1.8;    // tiles per frame
export const ENEMY_SPEED = 0.15;      // tiles per frame

// ---------------------------------------------------------------------------
// Game rules
// ---------------------------------------------------------------------------
export const INITIAL_LIVES = 3;

// Overlay durations (in milliseconds).
export const LEVEL_INTRO_DURATION_MS = 3000;
export const PLAYER_DEAD_DURATION_MS = 1500;
export const LEVEL_CLEAR_DURATION_MS = 1500;

// ---------------------------------------------------------------------------
// Input
// ---------------------------------------------------------------------------
// Terminals don't emit key-up events for arrow keys in raw mode. We treat
// "no repeat within this many ms" as "released" so a held arrow keeps
// moving but tapping produces a short burst.
export const INPUT_HOLD_TIMEOUT_MS = 150;

// ---------------------------------------------------------------------------
// Collision
// ---------------------------------------------------------------------------
// Solid tile characters. These block movement.
export const SOLID_TILE_CHARS = new Set(['#', 'B', '?']);

// ---------------------------------------------------------------------------
// Audio
// ---------------------------------------------------------------------------
// When true, game state changes print a BEL character (terminal bell).
// Can be toggled live from the pause screen with the M key.
export const DEFAULT_AUDIO = true;

// ---------------------------------------------------------------------------
// UI
// ---------------------------------------------------------------------------
// How long the very first start screen flash is, before drawing borders.
export const START_SCREEN_BORDER_WIDTH = 60;
