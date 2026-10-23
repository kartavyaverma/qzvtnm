import { describe, expect, it } from "vitest";
import { parseUrlState, serializeUrlState } from "./useUrlState";

describe("url state", () => {
  it("defaults to the decision view", () => {
    expect(parseUrlState("")).toEqual({ view: "decision", day: null, cutoff: null });
  });

  it("reads valid parameters", () => {
    expect(parseUrlState("?view=accuracy&day=2026-01-15&cutoff=09:50")).toEqual({
      view: "accuracy",
      day: "2026-01-15",
      cutoff: "09:50",
    });
  });

  it("ignores malformed parameters", () => {
    expect(parseUrlState("?view=admin&day=15-01-2026&cutoff=9")).toEqual({
      view: "decision",
      day: null,
      cutoff: null,
    });
  });

  it("round-trips through the query string", () => {
    const state = { view: "horizon", day: "2026-01-20", cutoff: "15:30" } as const;
    expect(parseUrlState(serializeUrlState(state))).toEqual(state);
  });
});
