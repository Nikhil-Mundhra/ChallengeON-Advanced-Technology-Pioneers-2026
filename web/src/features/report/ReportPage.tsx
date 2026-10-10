import { Link } from "react-router";
import { LIMITATIONS, NOWCAST_VALIDATION, PLANNING_HOLDOUT, QUESTION, SECTIONS, SUCCESS_CRITERIA, type ReportSection } from "../../content/report";
import { formatSigned } from "../../data/format";
import type { Bundle, Manifest } from "../../engine/types";
import { QuestionAnswers } from "../questions/QuestionAnswers";
import { useActiveSection } from "./useActiveSection";
import "./report.css";

const IDS = SECTIONS.map((s) => s.id);

/** Long-form, scrollable report: a hero band, then a raised sheet (its own layer) holding a sticky
 *  contents rail and the article. Static copy from content/report.ts; renders without the bundle. */
export function ReportPage({ manifest, bundle }: { manifest: Manifest | null; bundle?: Bundle | null }) {
  const active = useActiveSection(IDS);
  return (
    <div className="report">
      <header className="report__hero">
        <p className="report__eyebrow">ATP 2026 · Department of Culture and Tourism – Abu Dhabi challenge</p>
        <h1 className="report__question">{QUESTION}</h1>
        <dl className="report__figures">
          <Figure value="4.2% / 4.6%" label="daily guests error (WAPE), domestic / international" />
          <Figure value="20.6%" label="weekly scenario model error (WMAPE), 30 holdout weeks" />
          <Figure value="21" label="markets: 15 countries, 5 regional groups, domestic" />
        </dl>
        <Link className="pill pill--accent report__cta" to="/simulate">Open the simulator</Link>
      </header>

      <div className="report__sheet">
        <nav className="report__toc" aria-label="Report contents">
          <ol>
            {SECTIONS.map((s) => (
              <li key={s.id}><a href={`#${s.id}`} aria-current={active === s.id ? "location" : undefined}>{s.kicker}</a></li>
            ))}
          </ol>
        </nav>
        <article className="report__article">
          {SECTIONS.map((s) => <Section key={s.id} section={s} bundle={bundle ?? null} />)}
          <footer className="report__footer">
            {manifest ? `Numbers from model bundle ${manifest.version} (spec ${manifest.spec}).` : "Loading the model bundle…"}
          </footer>
        </article>
      </div>
    </div>
  );
}

function Figure({ value, label }: { value: string; label: string }) {
  return <div className="report__figure"><dt>{label}</dt><dd>{value}</dd></div>;
}

function Section({ section, bundle }: { section: ReportSection; bundle: Bundle | null }) {
  return (
    <section id={section.id} className="report__section" aria-labelledby={`${section.id}-title`}>
      <p className="report__kicker">{section.kicker}</p>
      <h2 id={`${section.id}-title`}>{section.title}</h2>
      {section.body.map((paragraph) => <p key={paragraph.slice(0, 32)}>{paragraph}</p>)}
      {section.id === "question" && <Criteria />}
      {section.id === "chain" && <ChainDiagram />}
      {section.id === "questions" && (bundle ? <QuestionAnswers planning={bundle.planning} weekly={bundle.weekly} /> : <p className="note">Loading the answers…</p>)}
      {section.id === "validation" && <ValidationTables />}
      {section.id === "sensitivity" && <Link className="pill pill--dark" to="/simulate">Run a scenario</Link>}
      {section.id === "limits" && (
        <ul className="report__callouts">{LIMITATIONS.map((text) => <li key={text}>{text}</li>)}</ul>
      )}
    </section>
  );
}

function Criteria() {
  return (
    <ol className="report__criteria" aria-label="Success criteria">
      {SUCCESS_CRITERIA.map((c) => (
        <li key={c.number} className="report__criterion">
          <span className="report__criterion-number">{c.number}</span>
          <strong>{c.title}</strong>
          <span>{c.text}</span>
        </li>
      ))}
    </ol>
  );
}

const LINKS = ["Seats", "Load factor", "Point-to-point share", "Response multiplier", "Guests per arrival"];
const STOCKS = ["Passengers", "P2P passengers", "Hotel arrivals", "Weekly guests"];

function ChainDiagram() {
  return (
    <figure className="report__chain">
      <ol>
        {LINKS.map((link, i) => (
          <li key={link}>
            <span className="report__chain-link">{link}</span>
            {i > 0 && <span className="report__chain-stock">→ {STOCKS[i - 1]}</span>}
          </li>
        ))}
      </ol>
      <figcaption>Each arrow multiplies by the next factor; a scenario edits one or more factors.</figcaption>
    </figure>
  );
}

function ValidationTables() {
  return (
    <div className="report__tables">
      <table className="table">
        <caption>Daily nowcast · {NOWCAST_VALIDATION.grain}</caption>
        <thead><tr><th scope="col">Model</th><th scope="col">Domestic</th><th scope="col">International</th></tr></thead>
        <tbody>
          {NOWCAST_VALIDATION.rows.map((r) => (
            <tr key={r.spec} className={r.shipped ? "table__row--highlight" : undefined}>
              <th scope="row">{r.spec}</th><td>{r.domestic.toFixed(2)}</td><td>{r.international.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <table className="table">
        <caption>Weekly scenario model · {PLANNING_HOLDOUT.grain}</caption>
        <thead><tr><th scope="col">Model</th><th scope="col">WMAPE %</th><th scope="col">Bias %</th></tr></thead>
        <tbody>
          {PLANNING_HOLDOUT.rows.map((r) => (
            <tr key={r.model} className={r.shipped ? "table__row--highlight" : undefined}>
              <th scope="row">{r.model}</th><td>{r.wmape.toFixed(2)}</td><td>{formatSigned(r.bias, (v) => v.toFixed(2))}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
