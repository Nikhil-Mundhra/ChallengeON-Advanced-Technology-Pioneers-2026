import type { ReactNode } from "react";

/** A titled group of controls inside a panel card, with an optional reset for the group. */
export function ControlSection({ title, onReset, resetDisabled, children }: {
  title: string; onReset?: () => void; resetDisabled?: boolean; children: ReactNode;
}) {
  return (
    <section className="control-section" aria-label={title}>
      <header className="control-section__head">
        <h3 className="control-section__title">{title}</h3>
        {onReset && <button type="button" className="control-section__reset" onClick={onReset} disabled={resetDisabled}>Reset</button>}
      </header>
      {children}
    </section>
  );
}
