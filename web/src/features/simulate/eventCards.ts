/** The stack of event cards over the moving map: newest on top, at most MAX, each fading after a
 *  lifetime that shortens with playback speed. Pure state, so the component only renders it. */

export interface EventCard { code: string; markets: string[]; firstWeek: string; lastWeek: string; remainingMs: number }
export interface WeekEvents { week: string; events: Array<{ code: string; markets: string[] }> }

export const MAX_CARDS = 4;
export const FADE_MS = 600;
export const lifetimeMs = (speed: number) => Math.round(4000 / Math.sqrt(speed));   // 1x: 4 s, 4x: 2 s

/** Playback moved one week forward: a continuing event extends its card and restarts its timer;
 *  a new one goes on top. */
export function advance(stack: EventCard[], week: WeekEvents, speed: number): EventCard[] {
  let next = [...stack];
  for (const e of week.events) {
    const open = next.find((c) => c.code === e.code);
    if (open) {
      next = next.filter((c) => c !== open);
      next.unshift({ ...open, lastWeek: week.week, markets: union(open.markets, e.markets), remainingMs: lifetimeMs(speed) });
    } else {
      next.unshift({ code: e.code, markets: e.markets, firstWeek: week.week, lastWeek: week.week, remainingMs: lifetimeMs(speed) });
    }
  }
  return next.slice(0, MAX_CARDS);
}

/** A jump (scrubber, reset, start week): only the landed week's events, so dragging never floods. */
export const jumpTo = (week: WeekEvents, speed: number): EventCard[] => advance([], week, speed);

/** Time passes only while playing; a paused stack keeps every card. */
export function tick(stack: EventCard[], elapsedMs: number, playing: boolean): EventCard[] {
  if (!playing) return stack;
  return stack.map((c) => ({ ...c, remainingMs: c.remainingMs - elapsedMs })).filter((c) => c.remainingMs > 0);
}

const union = (a: string[], b: string[]) => [...new Set([...a, ...b])];
