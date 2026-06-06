// Helpers for the live InputState object.

import type { InputState } from './types';

export function createInitialInputState(): InputState {
  return {
    left: false,
    right: false,
    jumpPressed: false,
    pausePressed: false,
    enterPressed: false,
    skipPressed: false,
    restartPressed: false,
    quitPressed: false,
  };
}

/** Clear the edge-triggered flags. Called once per game tick after processing. */
export function clearEdgeTriggers(input: InputState): void {
  input.jumpPressed = false;
  input.pausePressed = false;
  input.enterPressed = false;
  input.skipPressed = false;
  input.restartPressed = false;
  input.quitPressed = false;
}

/** Reset *everything* — held keys and edge flags. Used when the game
 *  transitions to a new state, so a key the player was holding at the moment
 *  of death or level clear does not carry into the next state. */
export function resetInput(input: InputState): void {
  input.left = false;
  input.right = false;
  input.jumpPressed = false;
  input.pausePressed = false;
  input.enterPressed = false;
  input.skipPressed = false;
  input.restartPressed = false;
  input.quitPressed = false;
}
