import { describe, expect, it } from "vitest";
import { formatGw, formatGwh, formatHour, formatMw, formatSignedGw, shiftDay } from "./format";

describe("number formatting", () => {
  it("formats megawatts and gigawatts", () => {
    expect(formatMw(12345.6)).toBe("12,346 MW");
    expect(formatGw(2038.9)).toBe("2.0 GW");
    expect(formatGwh(278630)).toBe("278.6 GWh");
  });

  it("shows a dash for missing values", () => {
    expect(formatMw(null)).toBe("–");
    expect(formatGw(undefined)).toBe("–");
    expect(formatGwh(Number.NaN)).toBe("–");
  });

  it("signs bias explicitly", () => {
    expect(formatSignedGw(1747)).toBe("+1.7 GW");
    expect(formatSignedGw(-550)).toBe("−0.6 GW");
    expect(formatSignedGw(0)).toBe("0.0 GW");
  });
});

describe("time formatting", () => {
  it("renders hours in UK local time", () => {
    expect(formatHour("2026-01-15T09:00:00Z")).toBe("09:00");
    expect(formatHour("2026-07-15T09:00:00Z")).toBe("10:00");
  });
});

describe("shiftDay", () => {
  const days = ["2026-01-02", "2026-01-03", "2026-01-04"];

  it("moves within the window", () => {
    expect(shiftDay(days, "2026-01-03", 1)).toBe("2026-01-04");
    expect(shiftDay(days, "2026-01-03", -1)).toBe("2026-01-02");
  });

  it("stops at the edges", () => {
    expect(shiftDay(days, "2026-01-04", 1)).toBeUndefined();
    expect(shiftDay(days, "2026-01-02", -1)).toBeUndefined();
    expect(shiftDay(days, "2025-12-31", 1)).toBeUndefined();
  });
});
