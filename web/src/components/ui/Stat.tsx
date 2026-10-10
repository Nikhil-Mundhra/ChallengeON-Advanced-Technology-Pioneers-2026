import type { ReactNode } from "react";

export function Stat({ value, caption }: { value: ReactNode; caption?: ReactNode }) {
  return (
    <div className="stat">
      <div className="stat__value">{value}</div>
      {caption && <div className="stat__caption">{caption}</div>}
    </div>
  );
}
