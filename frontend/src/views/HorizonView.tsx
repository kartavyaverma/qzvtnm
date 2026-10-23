import { useQuery } from "@tanstack/react-query";
import { horizonQuery } from "../api/queries";
import { HorizonChart } from "../charts/HorizonChart";
import { Callout, Card, ErrorState, Loading } from "../components/ui";
import { formatGw } from "../lib/format";

export function HorizonView({ cutoff }: { cutoff: string }) {
  const horizon = useQuery(horizonQuery(cutoff));

  if (horizon.isPending) return <Loading label="Loading horizon analysis" />;
  if (horizon.isError) return <ErrorState error={horizon.error} onRetry={() => void horizon.refetch()} />;

  const { buckets, decisionHorizonMin, decisionHorizonMax } = horizon.data;
  const first = buckets[0];
  const last = buckets.at(-1);

  return (
    <div className="view">
      <Callout>
        Forecasts get worse the further ahead they look: from <strong>{formatGw(first?.summary.mae)}</strong> average
        error {first?.startHours}–{first?.endHours} hours out to <strong>{formatGw(last?.summary.mae)}</strong> at{" "}
        {last?.startHours}–{last?.endHours} hours. A day-ahead buyer at {cutoff} is always looking{" "}
        {decisionHorizonMin?.toFixed(0)}–{decisionHorizonMax?.toFixed(0)} hours ahead.
      </Callout>
      <Card
        title="Forecast error vs lead time"
        subtitle="All Elexon WINDFOR publications for the analysis period, grouped by how far ahead they were made."
      >
        <HorizonChart horizon={horizon.data} />
      </Card>
    </div>
  );
}
