import type { ReactNode } from "react";
import { Card } from "./Card";
import { Stat } from "./Stat";

export type StatTone = "accent" | "secondary" | "neutral";

/** A headline number card: title, value, caption and an optional badge, with a coloured top rule. */
export function StatCard({ title, subtitle, value, caption, tone, badge }: {
  title: string; subtitle?: ReactNode; value: ReactNode; caption?: ReactNode; tone: StatTone; badge?: ReactNode;
}) {
  return (
    <Card title={title} subtitle={subtitle} className={`stat-card stat-card--${tone}`}>
      <Stat value={value} caption={caption} />
      {badge}
    </Card>
  );
}
