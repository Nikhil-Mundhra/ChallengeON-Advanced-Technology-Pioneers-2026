import { useId } from "react";

interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  format?: (value: number) => string;
  onChange: (value: number) => void;
}

export function Slider({ label, value, min, max, step = 1, format = String, onChange }: SliderProps) {
  const id = useId();
  return (
    <div className="slider">
      <label className="slider__label" htmlFor={id}>
        <span>{label}</span>
        <span className="slider__value">{format(value)}</span>
      </label>
      <input id={id} type="range" min={min} max={max} step={step} value={value}
             onChange={(event) => onChange(Number(event.target.value))} />
    </div>
  );
}
