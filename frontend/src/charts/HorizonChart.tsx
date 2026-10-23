import { useMemo } from "react";
import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Horizon } from "../api/types";
import { formatGw } from "../lib/format";
import { axisProps, colors, gwTick } from "./theme";

export function HorizonChart({ horizon }: { horizon: Horizon }) {
  const data = useMemo(
    () =>
      horizon.buckets.map((b) => ({
        mid: (b.startHours + b.endHours) / 2,
        label: `${b.startHours}–${b.endHours}h`,
        mae: b.summary.mae,
        p95: b.summary.p95AbsError,
        bias: b.summary.bias,
      })),
    [horizon],
  );

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 16, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid stroke={colors.grid} vertical={false} />
        <XAxis
          dataKey="mid"
          type="number"
          domain={[0, "dataMax + 3"]}
          tickFormatter={(v: number) => `${v}h`}
          label={{ value: "Hours between forecast publication and delivery", position: "insideBottom", offset: -4, fill: "#64748b" }}
          {...axisProps}
        />
        <YAxis tickFormatter={gwTick} width={44} {...axisProps} />
        {horizon.decisionHorizonMin !== null && horizon.decisionHorizonMax !== null && (
          <ReferenceArea
            x1={horizon.decisionHorizonMin}
            x2={horizon.decisionHorizonMax}
            fill={colors.accent}
            fillOpacity={0.12}
            label={{ value: "Your decision window", position: "insideTop", fill: "#b45309", fontSize: 12 }}
          />
        )}
        <Tooltip
          labelFormatter={(_, payload) => String(payload?.[0]?.payload?.label ?? "")}
          formatter={(v, n) => [formatGw(Number(v)), n]}
        />
        <Legend verticalAlign="top" />
        <Line dataKey="mae" name="Mean absolute error" stroke={colors.forecast} strokeWidth={2.5} isAnimationActive={false} />
        <Line dataKey="p95" name="95th percentile error" stroke={colors.over} strokeDasharray="5 4" isAnimationActive={false} />
        <Line dataKey="bias" name="Bias" stroke={colors.accent} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
