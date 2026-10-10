import { Card } from "../../components/ui";
import { SEASON_NAMES } from "../../content/labels";
import { formatFull, formatSigned, toneOf } from "../../data/format";
import { weeklyHeadline, type Lever, type Planning } from "../../engine/planning";

/** For a country without flights or hotel history: weekly guests per season with the levers, from
 *  similar markets' patterns (no past weeks to total or check against). */
export function NewRouteCard({ planning, market, lever, seasons }: { planning: Planning; market: string; lever: Lever; seasons: string[] }) {
  const rows = seasons.map((s) => ({ season: s, ...weeklyHeadline(planning, market, s, lever) }));
  const noFlights = rows.every((r) => r.sim === 0);
  return (
    <Card title="New route estimate" subtitle="Hotel guests per week, from similar markets">
      {noFlights
        ? <p className="note">No route of its own yet. Add weekly flights on the left to see what a new route would bring.</p>
        : (
          <table className="table">
            <thead><tr><th scope="col">Season</th><th scope="col">Guests a week</th><th scope="col">Change</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.season}>
                  <th scope="row">{SEASON_NAMES[r.season] ?? r.season}</th>
                  <td>{formatFull(r.sim)}</td>
                  <td className={toneOf(r.change)}>{formatSigned(r.change)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      <p className="note">±{Math.round(rows[0].errorPct * 100)}% error at best; a new route has no past weeks to check against.</p>
    </Card>
  );
}
