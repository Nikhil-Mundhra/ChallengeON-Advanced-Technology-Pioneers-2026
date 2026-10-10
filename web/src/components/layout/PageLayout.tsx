import type { ReactNode } from "react";
import "./page.css";

/** A page with a sticky settings column on the left and the results on the right. */
export function PageLayout({ aside, asideLabel, children }: { aside: ReactNode; asideLabel: string; children: ReactNode }) {
  return (
    <div className="page">
      <aside className="page__aside" aria-label={asideLabel}>{aside}</aside>
      <div className="page__main">{children}</div>
    </div>
  );
}
