import { useMemo } from "react";
import { Link } from "react-router";
import { marketName, SEASON_NAMES } from "../../content/labels";
import { QUESTIONS } from "../../content/questions";
import { formatCount, formatSigned, formatShare } from "../../data/format";
import type { Planning } from "../../engine/planning";
import { answerQuestions, type LeverAnswer, type MixAnswer } from "../../engine/questions";
import type { Weekly } from "../../engine/weekly";
import "./questions.css";

/** What if…? The five planning questions, each answered in one sentence from the live model.
 *  Used by the landing page and the report page. */
export function QuestionAnswers({ planning, weekly }: { planning: Planning; weekly: Weekly }) {
  const a = useMemo(() => answerQuestions(planning, weekly), [planning, weekly]);
  return (
    <ol className="questions">
      <Question q={QUESTIONS.newRoute} figure={a.newRoute}>
        A new route from {marketName(a.newRoute.market)} with 3 flights a week of 300 seats (900 seats) would bring about{" "}
        <strong>{visitors(a.newRoute)}</strong> in {season(a.newRoute)}, judged from similar markets.
      </Question>
      <Question q={QUESTIONS.frequency} figure={a.frequency}>
        Two more weekly flights from the {marketName(a.frequency.market)} (290 seats each) would add about{" "}
        <strong>{visitors(a.frequency)}</strong> in {season(a.frequency)}
        {year(a.frequency)}. Fewer flights work the same way in reverse.
      </Question>
      <Question q={QUESTIONS.seats} figure={a.seats}>
        10% more seats on today's flights from {marketName(a.seats.market)} would add about{" "}
        <strong>{visitors(a.seats)}</strong> in {season(a.seats)}{year(a.seats)}.
      </Question>
      <Question q={QUESTIONS.fuller} figure={a.fuller}>
        If flights from {marketName(a.fuller.market)} were 5 points fuller, expect about{" "}
        <strong>{visitors(a.fuller)}</strong> in {season(a.fuller)}{year(a.fuller)}.
      </Question>
      <li className="question">
        <p className="question__q">{QUESTIONS.mix}</p>
        <p className="question__a">Yes. {a.mix.map((m) => mixSentence(m)).join(" ")}</p>
        <Link to="/simulate" className="question__try">See it move on the map</Link>
      </li>
    </ol>
  );
}

const season = (x: LeverAnswer) => (SEASON_NAMES[x.season] ?? x.season).toLowerCase();
const visitors = (x: LeverAnswer) =>
  `${formatCount(Math.round(x.visitorsPerWeek / 10) * 10)} more hotel visitors a week, staying ${formatCount(Math.round(x.perWeek / 10) * 10)} nights in all,`;
const year = (x: LeverAnswer) => (x.perYear === null ? "" : `; about ${formatSigned(x.perYear, formatCount)} hotel nights over ${x.year}`);
const mixSentence = (m: MixAnswer) =>
  `In ${(SEASON_NAMES[m.season] ?? m.season).toLowerCase()} the biggest sources are ${m.top.map((t) => `${marketName(t.market)} (${formatShare(t.share, 0)})`).join(", ")}.`;

function Question({ q, figure, children }: { q: string; figure: LeverAnswer; children: React.ReactNode }) {
  return (
    <li className="question">
      <p className="question__q">{q}</p>
      <p className="question__a">{children}</p>
      <p className="question__note">±{Math.round(figure.errorPct * 100)}% error on the weekly figure.</p>
      <Link to="/simulate" className="question__try">Try your own numbers</Link>
    </li>
  );
}
