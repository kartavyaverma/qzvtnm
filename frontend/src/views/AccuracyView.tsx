import { useQueries, useQuery } from "@tanstack/react-query";
import { accuracyQuery } from "../api/queries";
import type { Meta } from "../api/types";
import { DailyErrorChart, HistogramChart, HourlyErrorChart, SeriesChart } from "../charts/AccuracyCharts";
import { Callout, Card, ErrorState, Loading, Stat, StatGrid } from "../components/ui";
import { formatDay, formatGw, formatPct, formatSignedGw } from "../lib/format";

interface Props {
  meta: Meta;
  cutoff: string;
}

function CutoffComparison({ meta }: { meta: Meta }) {
  const results = useQueries({ queries: meta.cutoffPresets.map((p) => accuracyQuery(p.cutoff)) });
  return (
    <table className="table">
      <thead>
        <tr>
          <th scope="col">Cutoff</th>
          <th scope="col">MAE</th>
          <th scope="col">RMSE</th>
          <th scope="col">Bias</th>
          <th scope="col">P90 shortfall</th>
        </tr>
      </thead>
      <tbody>
        {meta.cutoffPresets.map((preset, index) => {
          const summary = results[index]?.data?.summary;
          return (
            <tr key={preset.cutoff}>
              <th scope="row">
                {preset.label} <span className="muted">{preset.cutoff}</span>
              </th>
              <td>{formatGw(summary?.mae)}</td>
              <td>{formatGw(summary?.rmse)}</td>
              <td>{formatSignedGw(summary?.bias)}</td>
              <td>{formatGw(summary?.p90Error)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export function AccuracyView({ meta, cutoff }: Props) {
  const accuracy = useQuery(accuracyQuery(cutoff));

  if (accuracy.isPending) return <Loading label="Loading accuracy analysis" />;
  if (accuracy.isError) return <ErrorState error={accuracy.error} onRetry={() => void accuracy.refetch()} />;

  const { summary, errorQuantiles, deliveryStart, deliveryEnd } = accuracy.data;
  const buffer = errorQuantiles.p90 ?? null;

  return (
    <div className="view">
      <Callout>
        Across {summary.count} delivery hours ({formatDay(deliveryStart)} to {formatDay(deliveryEnd)}), the forecast
        available at {cutoff} was off by <strong>{formatGw(summary.mae)}</strong> on average and ran{" "}
        <strong>{(summary.bias ?? 0) > 0 ? "high" : "low"}</strong> {formatPct(summary.overForecastSharePct, 0)} of the
        time. Planning for wind <strong>{formatGw(buffer)}</strong> below the forecast would have covered the shortfall
        in 90% of hours.
      </Callout>

      <StatGrid>
        <Stat label="Mean absolute error" value={formatGw(summary.mae)} hint={`${formatPct(summary.nmaePct)} of mean output`} tone="accent" />
        <Stat label="RMSE" value={formatGw(summary.rmse)} hint="Penalises large misses" />
        <Stat label="Bias" value={formatSignedGw(summary.bias)} hint="Positive = forecast too high" tone="warn" />
        <Stat label="P90 shortfall buffer" value={formatGw(buffer)} hint="Covers 9 in 10 hours" />
        <Stat label="Worst over-forecast" value={formatGw(summary.maxOverForecast)} hint="Single hour" />
      </StatGrid>

      <Card title="Forecast vs actual, whole period" subtitle="Each point is the forecast a buyer had at the cutoff for that hour.">
        <SeriesChart series={accuracy.data.series} />
      </Card>

      <div className="grid-2">
        <Card title="Error by delivery day" subtitle="Bars: average size of the miss. Line: direction of the miss.">
          <DailyErrorChart byDay={accuracy.data.byDay} />
        </Card>
        <Card title="Error distribution" subtitle="Red: wind came in below forecast (need to buy more). Blue: above.">
          <HistogramChart histogram={accuracy.data.histogram} />
        </Card>
      </div>

      <div className="grid-2">
        <Card title="Error by hour of day" subtitle="UK local hour of delivery. Shows which parts of the day need the biggest buffer.">
          <HourlyErrorChart byHour={accuracy.data.byHour} />
        </Card>
        <Card title="Does a later cutoff help?" subtitle="Same period, scored at each auction gate closure.">
          <CutoffComparison meta={meta} />
        </Card>
      </div>
    </div>
  );
}
