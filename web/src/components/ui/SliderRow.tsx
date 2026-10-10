import { useId } from "react";

interface SliderRowProps {
  label: string;
  hint?: string;
  value: number;
  defaultValue: number;
  min: number;
  max: number;
  step?: number;
  format?: (value: number) => string;
  onChange: (value: number) => void;
}

const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));
const roundTo = (v: number, step: number) => Number((Math.round(v / step) * step).toFixed(6));

/** One controlled slider: label and value on top, -/+ steppers either side of the track, the
 *  default marked on the track, min/max below. A changed value shows a dot and its own reset. */
export function SliderRow({ label, hint, value, defaultValue, min, max, step = 1, format = String, onChange }: SliderRowProps) {
  const id = useId();
  const changed = value !== defaultValue;
  const set = (v: number) => onChange(roundTo(clamp(v, min, max), step));
  const mark = ((defaultValue - min) / (max - min)) * 100;
  return (
    <div className={`slider-row${changed ? " slider-row--changed" : ""}`}>
      <div className="slider-row__head">
        <label htmlFor={id} className="slider-row__label">
          {label}
          {hint && <span className="slider-row__hint">{hint}</span>}
        </label>
        <span className="slider-row__value">
          {changed && <button type="button" className="slider-row__reset" onClick={() => onChange(defaultValue)} aria-label={`Reset ${label}`}>reset</button>}
          {format(value)}
        </span>
      </div>
      <div className="slider-row__control">
        <button type="button" className="slider-row__step" onClick={() => set(value - step)} disabled={value <= min} aria-label={`Decrease ${label}`}>−</button>
        <div className="slider-row__track">
          <input id={id} type="range" min={min} max={max} step={step} value={value} onChange={(e) => set(Number(e.target.value))} />
          <span className="slider-row__mark" style={{ left: `${mark}%` }} aria-hidden="true" />
        </div>
        <button type="button" className="slider-row__step" onClick={() => set(value + step)} disabled={value >= max} aria-label={`Increase ${label}`}>+</button>
      </div>
      <div className="slider-row__scale" aria-hidden="true"><span>{format(min)}</span><span>{format(max)}</span></div>
    </div>
  );
}
