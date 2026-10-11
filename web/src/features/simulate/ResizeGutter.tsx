import { useCallback, useEffect, useState, type KeyboardEvent, type PointerEvent, type RefObject } from "react";

interface ResizeGutterProps {
  id: "panel" | "results";
  label: string;
  value: number;
  defaultValue: number;
  min: number;
  max: number;
  onResize: (newWidth: number) => void;
  onReset: () => void;
  workbenchRef: RefObject<HTMLDivElement | null>;
  onDragStateChange?: (dragging: boolean) => void;
}

/** Draggable splitter between workbench widgets with pointer capture and keyboard steps. */
export function ResizeGutter({
  id,
  label,
  value,
  defaultValue,
  min,
  max,
  onResize,
  onReset,
  workbenchRef,
  onDragStateChange,
}: ResizeGutterProps) {
  const [isDragging, setIsDragging] = useState(false);

  const notifyDrag = useCallback((dragging: boolean) => {
    setIsDragging(dragging);
    onDragStateChange?.(dragging);
  }, [onDragStateChange]);

  const handlePointerDown = (e: PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    notifyDrag(true);
  };

  const handlePointerMove = (e: PointerEvent<HTMLDivElement>) => {
    if (!isDragging || !workbenchRef.current) return;
    const rect = workbenchRef.current.getBoundingClientRect();
    const effectiveMax = Math.min(max, Math.floor(rect.width * (id === "panel" ? 0.45 : 0.38)));
    const computed = id === "panel" ? e.clientX - rect.left : rect.right - e.clientX;
    onResize(Math.min(effectiveMax, Math.max(min, Math.round(computed))));
  };

  const stopDrag = (e: PointerEvent<HTMLDivElement>) => {
    if (isDragging) {
      notifyDrag(false);
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
      } catch {
        // pointer capture already dropped
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const step = e.shiftKey ? 25 : 10;
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      onResize(Math.min(max, Math.max(min, value + (id === "panel" ? -step : step))));
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      onResize(Math.min(max, Math.max(min, value + (id === "panel" ? step : -step))));
    } else if (e.key === "Home") {
      e.preventDefault();
      onResize(min);
    } else if (e.key === "End") {
      e.preventDefault();
      onResize(max);
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onReset();
    }
  };

  useEffect(() => {
    return () => {
      if (isDragging) notifyDrag(false);
    };
  }, [isDragging, notifyDrag]);

  return (
    <div
      role="separator"
      tabIndex={0}
      aria-orientation="vertical"
      aria-label={label}
      aria-valuenow={value}
      aria-valuemin={min}
      aria-valuemax={max}
      title={`${label} (drag to resize, double-click to reset to ${defaultValue}px)`}
      className={`workbench__resizer workbench__resizer--${id}${isDragging ? " workbench__resizer--active" : ""}`}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={stopDrag}
      onPointerCancel={stopDrag}
      onDoubleClick={onReset}
      onKeyDown={handleKeyDown}
    >
      <span className="workbench__resizer-handle" />
    </div>
  );
}
