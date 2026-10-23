import { useEffect, useState } from "react";
import type { CutoffPreset } from "../api/types";
import { formatDay, shiftDay } from "../lib/format";

interface DayStepperProps {
  days: string[];
  value: string;
  onChange: (day: string) => void;
}

export function DayStepper({ days, value, onChange }: DayStepperProps) {
  const previous = shiftDay(days, value, -1);
  const next = shiftDay(days, value, 1);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target && ["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName)) return;
      if (event.key === "ArrowLeft" && previous) onChange(previous);
      if (event.key === "ArrowRight" && next) onChange(next);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [previous, next, onChange]);

  return (
    <div className="stepper" role="group" aria-label="Delivery day">
      <button
        type="button"
        className="icon-button"
        onClick={() => previous && onChange(previous)}
        disabled={!previous}
        aria-label="Previous delivery day"
      >
        ‹
      </button>
      <select value={value} onChange={(event) => onChange(event.target.value)} aria-label="Select delivery day">
        {days.map((day) => (
          <option key={day} value={day}>
            {formatDay(day)}
          </option>
        ))}
      </select>
      <button
        type="button"
        className="icon-button"
        onClick={() => next && onChange(next)}
        disabled={!next}
        aria-label="Next delivery day"
      >
        ›
      </button>
    </div>
  );
}

interface CutoffPickerProps {
  presets: CutoffPreset[];
  value: string;
  onChange: (cutoff: string) => void;
}

export function CutoffPicker({ presets, value, onChange }: CutoffPickerProps) {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);

  return (
    <div className="cutoff" role="group" aria-label="Decision cutoff">
      <span className="control-label">Decision cutoff (D-1, UK time)</span>
      <div className="chips">
        {presets.map((preset) => (
          <button
            key={preset.cutoff}
            type="button"
            className={`chip ${preset.cutoff === value ? "chip-active" : ""}`}
            aria-pressed={preset.cutoff === value}
            title={preset.description}
            onClick={() => onChange(preset.cutoff)}
          >
            {preset.label} · {preset.cutoff}
          </button>
        ))}
        <input
          type="time"
          className="time-input"
          value={draft}
          aria-label="Custom cutoff time"
          onChange={(event) => setDraft(event.target.value)}
          onBlur={() => draft && draft !== value && onChange(draft)}
          onKeyDown={(event) => event.key === "Enter" && draft && onChange(draft)}
        />
      </div>
    </div>
  );
}
