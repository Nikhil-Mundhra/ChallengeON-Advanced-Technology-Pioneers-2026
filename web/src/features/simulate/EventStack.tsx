import { useEffect, useRef, useState } from "react";
import { eventName, marketName } from "../../content/labels";
import { formatDate } from "../../data/format";
import { advance, FADE_MS, jumpTo, tick, type EventCard, type WeekEvents } from "./eventCards";

const TICK_MS = 100;
const DAY = 86_400_000;
const weekEnd = (monday: string) => new Date(Date.parse(`${monday}T00:00:00Z`) + 6 * DAY).toISOString().slice(0, 10);

/** Event cards stacked over the map while the weeks play. Stepping one week forward adds or extends
 *  a card; any other move of the week (scrubber, reset) shows only that week's events. */
export function EventStack({ weeks, index, playing, speed, totalMarkets }: {
  weeks: WeekEvents[]; index: number; playing: boolean; speed: number; totalMarkets: number;
}) {
  const [stack, setStack] = useState<EventCard[]>([]);
  const previous = useRef(index);

  useEffect(() => {
    const step = index - previous.current;
    previous.current = index;
    const week = weeks[index];
    if (!week) return;
    setStack((s) => (step === 1 && playing ? advance(s, week, speed) : jumpTo(week, speed)));
  }, [index]);   // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setStack((s) => tick(s, TICK_MS, true)), TICK_MS);
    return () => clearInterval(id);
  }, [playing]);

  if (!stack.length) return null;
  return (
    <ol className="event-stack" aria-live="polite" aria-label="Events in the weeks shown">
      {stack.map((c) => (
        <li key={c.code} className={`event-stack__card${c.remainingMs < FADE_MS && playing ? " event-stack__card--leaving" : ""}`}>
          <span className="event-stack__name">{eventName(c.code)}</span>
          <span className="event-stack__when">
            {c.firstWeek === c.lastWeek ? `week of ${formatDate(c.firstWeek)}` : `${formatDate(c.firstWeek)} to ${formatDate(weekEnd(c.lastWeek))}`}
          </span>
          <span className="event-stack__who">
            {c.markets.length >= totalMarkets ? "all markets" : c.markets.slice(0, 2).map(marketName).join(", ") + (c.markets.length > 2 ? ` +${c.markets.length - 2}` : "")}
          </span>
        </li>
      ))}
    </ol>
  );
}
