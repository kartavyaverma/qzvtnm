import { useCallback, useSyncExternalStore } from "react";

export type View = "decision" | "accuracy" | "horizon";

export interface UrlState {
  view: View;
  day: string | null;
  cutoff: string | null;
}

const VIEWS: readonly View[] = ["decision", "accuracy", "horizon"];
const DAY_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const CUTOFF_PATTERN = /^\d{2}:\d{2}$/;

export function parseUrlState(search: string): UrlState {
  const params = new URLSearchParams(search);
  const view = params.get("view");
  const day = params.get("day");
  const cutoff = params.get("cutoff");
  return {
    view: VIEWS.includes(view as View) ? (view as View) : "decision",
    day: day && DAY_PATTERN.test(day) ? day : null,
    cutoff: cutoff && CUTOFF_PATTERN.test(cutoff) ? cutoff : null,
  };
}

export function serializeUrlState(state: UrlState): string {
  const params = new URLSearchParams();
  params.set("view", state.view);
  if (state.day) params.set("day", state.day);
  if (state.cutoff) params.set("cutoff", state.cutoff);
  return `?${params.toString()}`;
}

function subscribe(onChange: () => void): () => void {
  window.addEventListener("popstate", onChange);
  return () => window.removeEventListener("popstate", onChange);
}

const getSearch = () => window.location.search;

export function useUrlState(): [UrlState, (patch: Partial<UrlState>) => void] {
  const search = useSyncExternalStore(subscribe, getSearch, () => "");
  const state = parseUrlState(search);

  const update = useCallback((patch: Partial<UrlState>) => {
    const next = serializeUrlState({ ...parseUrlState(window.location.search), ...patch });
    if (next === window.location.search) return;
    window.history.pushState(null, "", next);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, []);

  return [state, update];
}
