import { Avatar, Card } from "../../components/ui";
import { formatFull, formatShare, titleCase } from "../../data/format";
import { nationalityTotals } from "../../engine/nowcastViews";
import type { Nowcast } from "../../engine/types";

/** International nationalities ranked by forecast guests over the days (point forecasts). */
export function NationalityList({ nowcast, start, end, filter }: { nowcast: Nowcast; start: string; end: string; filter: string }) {
  const rows = nationalityTotals(nowcast, start, end).filter((row) => row.name.toLowerCase().includes(filter.toLowerCase())).slice(0, 8);
  const top = rows[0]?.guests || 1;
  return (
    <Card title="Nationalities" subtitle="Forecast international guests for these days">
      <ul className="nationality-list">
        {rows.map((row) => (
          <li key={row.name} className="nationality-list__row">
            <Avatar name={row.name} />
            <div className="nationality-list__text">
              <span className="nationality-list__name">{titleCase(row.name)}</span>
              <span className="nationality-list__bar"><span style={{ width: `${(row.guests / top) * 100}%` }} /></span>
            </div>
            <div className="nationality-list__value">
              <span>{formatFull(row.guests)}</span>
              <span className="nationality-list__share">{formatShare(row.share)}</span>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
