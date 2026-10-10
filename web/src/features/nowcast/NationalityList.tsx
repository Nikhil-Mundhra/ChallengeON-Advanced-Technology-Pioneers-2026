import { Avatar, Card } from "../../components/ui";
import { formatFull, titleCase } from "../../data/format";
import type { Nowcast } from "../../engine/types";

/** International nationalities ranked by predicted guests over the range (point predictions). */
export function NationalityList({ nowcast, start, end, filter }: { nowcast: Nowcast; start: string; end: string; filter: string }) {
  const totals = Object.entries(nowcast.nationalities).map(([name, values]) => {
    let guests = 0;
    values.date.forEach((d, i) => { if (d >= start && d <= end) guests += values.pred[i]; });
    return { name, guests };
  });
  const all = totals.reduce((sum, row) => sum + row.guests, 0);
  const rows = totals.filter((row) => row.name.toLowerCase().includes(filter.toLowerCase()))
    .sort((a, b) => b.guests - a.guests).slice(0, 8);
  return (
    <Card title="Nationalities" subtitle="International guests in the range, as predicted">
      <ul className="nationality-list">
        {rows.map((row) => (
          <li key={row.name} className="nationality-list__row">
            <Avatar name={row.name} />
            <div className="nationality-list__text">
              <span className="nationality-list__name">{titleCase(row.name)}</span>
              <span className="nationality-list__bar"><span style={{ width: `${(row.guests / (rows[0]?.guests || 1)) * 100}%` }} /></span>
            </div>
            <div className="nationality-list__value">
              <span>{formatFull(row.guests)}</span>
              <span className="nationality-list__share">{all ? `${((row.guests / all) * 100).toFixed(1)}%` : ""}</span>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
