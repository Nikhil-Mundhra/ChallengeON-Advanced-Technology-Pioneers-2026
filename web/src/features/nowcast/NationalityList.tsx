import { useState } from "react";
import { Icon } from "../../components/layout/icons";
import { Avatar, Card } from "../../components/ui";
import { formatDate, formatFull, formatShare, titleCase } from "../../data/format";
import { nationalityTotals } from "../../engine/nowcastViews";
import type { Nowcast } from "../../engine/types";

/** International nationalities ranked by forecast guests over the days (point forecasts). */
export function NationalityList({ nowcast, start, end }: { nowcast: Nowcast; start: string; end: string }) {
  const [filter, setFilter] = useState("");
  const rows = nationalityTotals(nowcast, start, end).filter((row) => row.name.toLowerCase().includes(filter.toLowerCase())).slice(0, 8);
  const top = rows[0]?.guests || 1;

  const searchBox = (
    <label className="nationalities__search">
      <Icon name="search" size={14} />
      <span className="visually-hidden">Search nationalities</span>
      <input
        type="search"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Search nationalities"
      />
    </label>
  );

  return (
    <Card
      title="Nationalities"
      subtitle={`Forecast international guests (${formatDate(start)} → ${formatDate(end)})`}
      actions={searchBox}
    >
      {rows.length === 0 ? (
        <p className="note" style={{ padding: "var(--space-3) 0" }}>No nationalities match "{filter}".</p>
      ) : (
        <ul className="nationality-list">
          {rows.map((row, index) => (
            <li key={row.name} className="nationality-list__row">
              <span className="nationality-list__rank" aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
              <Avatar name={row.name} />
              <div className="nationality-list__text">
                <span className="nationality-list__name">{titleCase(row.name)}</span>
                <span className="nationality-list__bar"><span style={{ width: `${(row.guests / top) * 100}%` }} /></span>
              </div>
              <div className="nationality-list__value">
                <span className="nationality-list__count">{formatFull(row.guests)}</span>
                <span className="nationality-list__share">{formatShare(row.share)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
