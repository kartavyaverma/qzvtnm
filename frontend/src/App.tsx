import { useCallback } from "react";
import { useMeta } from "./api/queries";
import { CutoffPicker } from "./components/Controls";
import { ErrorState, Loading } from "./components/ui";
import { useUrlState, type View } from "./state/useUrlState";
import { AccuracyView } from "./views/AccuracyView";
import { DecisionView } from "./views/DecisionView";
import { HorizonView } from "./views/HorizonView";

const TABS: { id: View; label: string; description: string }[] = [
  { id: "decision", label: "Decision day", description: "What the buyer saw" },
  { id: "accuracy", label: "Forecast accuracy", description: "How wrong it was" },
  { id: "horizon", label: "Lead time", description: "Why timing matters" },
];

export default function App() {
  const meta = useMeta();
  const [state, setState] = useUrlState();
  const onDayChange = useCallback((day: string) => setState({ day }), [setState]);

  if (meta.isPending) return <Loading label="Starting Windcast" />;
  if (meta.isError) return <ErrorState error={meta.error} onRetry={() => void meta.refetch()} />;

  const days = meta.data.deliveryDays;
  const day = state.day && days.includes(state.day) ? state.day : (days[Math.floor(days.length / 2)] ?? days[0]!);
  const cutoff = state.cutoff ?? meta.data.defaultCutoff;

  return (
    <div className="app">
      <header className="masthead">
        <div className="brand">
          <span className="logo" aria-hidden="true" />
          <div>
            <h1>Windcast</h1>
            <p className="muted">GB wind forecasts for day-ahead purchasing · January 2026 decisions</p>
          </div>
        </div>
        <CutoffPicker presets={meta.data.cutoffPresets} value={cutoff} onChange={(c) => setState({ cutoff: c })} />
      </header>

      <nav className="tabs" aria-label="Views">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`tab ${state.view === tab.id ? "tab-active" : ""}`}
            aria-current={state.view === tab.id ? "page" : undefined}
            onClick={() => setState({ view: tab.id })}
          >
            <span>{tab.label}</span>
            <small>{tab.description}</small>
          </button>
        ))}
      </nav>

      <main>
        {state.view === "decision" && (
          <DecisionView meta={meta.data} day={day} cutoff={cutoff} onDayChange={onDayChange} />
        )}
        {state.view === "accuracy" && <AccuracyView meta={meta.data} cutoff={cutoff} />}
        {state.view === "horizon" && <HorizonView cutoff={cutoff} />}
      </main>

      <footer className="footer muted">
        Data: {meta.data.sources.actuals}; {meta.data.sources.forecasts}. Times in UK local time. {meta.data.errorConvention}.
      </footer>
    </div>
  );
}
