import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { decisionQuery, vintagesQuery } from "../api/queries";
import type { Meta } from "../api/types";
import { DecisionChart } from "../charts/DecisionChart";
import { EvolutionChart } from "../charts/EvolutionChart";
import { DayStepper } from "../components/Controls";
import { Callout, Card, ErrorState, Loading, Stat, StatGrid } from "../components/ui";
import { formatDay, formatGwh, formatPct, formatSignedGw, formatGw, formatStamp, shiftDay } from "../lib/format";

interface Props {
  meta: Meta;
  day: string;
  cutoff: string;
  onDayChange: (day: string) => void;
}

export function DecisionView({ meta, day, cutoff, onDayChange }: Props) {
  const [showActual, setShowActual] = useState(true);
  const queryClient = useQueryClient();
  const decision = useQuery(decisionQuery(day, cutoff));
  const vintages = useQuery(vintagesQuery(day, cutoff));

  useEffect(() => {
    for (const step of [-1, 1]) {
      const neighbour = shiftDay(meta.deliveryDays, day, step);
      if (neighbour) void queryClient.prefetchQuery(decisionQuery(neighbour, cutoff));
    }
  }, [day, cutoff, meta.deliveryDays, queryClient]);

  const data = decision.data;
  const publishedAt = data?.forecastPublishTimes.at(-1);
  const horizons = data?.points.map((p) => p.horizonHours) ?? [];

  return (
    <div className="view">
      <div className="toolbar">
        <DayStepper days={meta.deliveryDays} value={day} onChange={onDayChange} />
        <label className="toggle">
          <input type="checkbox" checked={showActual} onChange={(e) => setShowActual(e.target.checked)} />
          Show actual generation (hindsight)
        </label>
      </div>

      {decision.isPending && <Loading label="Loading decision data" />}
      {decision.isError && <ErrorState error={decision.error} onRetry={() => void decision.refetch()} />}

      {data && (
        <>
          <Callout>
            Buying for <strong>{formatDay(data.deliveryDay)}</strong> at <strong>{data.cutoff}</strong> on{" "}
            {formatDay(data.decisionDay)}, the latest wind forecast available was published{" "}
            <strong>{publishedAt ? formatStamp(publishedAt) : "–"}</strong>, covering{" "}
            {Math.min(...horizons).toFixed(1)}–{Math.max(...horizons).toFixed(1)} hours ahead.
          </Callout>

          <StatGrid>
            <Stat label="Forecast wind energy" value={formatGwh(data.energy.forecastMwh)} tone="accent" />
            <Stat
              label="Prudent plan (P10 wind)"
              value={formatGwh(data.energy.conservativeMwh)}
              hint={data.bandAvailable ? `From errors of ${data.historyDays} earlier days` : "Not enough history yet"}
            />
            <Stat label="Actual wind energy" value={formatGwh(data.energy.actualMwh)} hint="Known only after delivery" />
            <Stat
              label="Day bias"
              value={formatSignedGw(data.summary.bias)}
              hint={(data.summary.bias ?? 0) > 0 ? "Forecast too high: shortfall risk" : "Forecast too low: surplus"}
              tone={(data.summary.bias ?? 0) > 0 ? "warn" : "good"}
            />
            <Stat
              label="Mean absolute error"
              value={formatGw(data.summary.mae)}
              hint={`${formatPct(data.summary.nmaePct)} of mean output`}
            />
          </StatGrid>

          <Card
            title="Forecast available at decision time"
            subtitle="Hourly wind generation, Great Britain. Shaded range shows where actual output landed 80% of the time on earlier days."
          >
            <DecisionChart points={data.points} showActual={showActual} />
          </Card>
        </>
      )}

      <Card
        title="How the forecast evolved"
        subtitle="Every Elexon publication covering this day. Solid teal lines were available before the cutoff; grey dashed lines arrived too late. The bold line is the one used."
      >
        {vintages.isPending && <Loading label="Loading forecast history" />}
        {vintages.isError && <ErrorState error={vintages.error} onRetry={() => void vintages.refetch()} />}
        {vintages.data && <EvolutionChart vintages={vintages.data} />}
      </Card>
    </div>
  );
}
