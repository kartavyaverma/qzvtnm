import { useMemo } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DecisionPoint } from "../api/types";
import { formatHour, formatMw } from "../lib/format";
import { axisProps, colors, gwTick } from "./theme";

interface Props {
  points: DecisionPoint[];
  showActual: boolean;
}

export function DecisionChart({ points, showActual }: Props) {
  const data = useMemo(
    () =>
      points.map((p) => ({
        time: p.time,
        forecast: p.forecast,
        actual: p.actual,
        band: p.low !== null && p.high !== null ? [p.low, p.high] : null,
      })),
    [points],
  );

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={colors.grid} vertical={false} />
        <XAxis dataKey="time" tickFormatter={formatHour} interval={2} {...axisProps} />
        <YAxis tickFormatter={gwTick} width={44} {...axisProps} label={{ value: "GW", angle: -90, position: "insideLeft", fill: "#64748b" }} />
        <Tooltip
          labelFormatter={(label) => `Hour starting ${formatHour(String(label))}`}
          formatter={(value, name) =>
            Array.isArray(value)
              ? [`${formatMw(Number(value[0]))} – ${formatMw(Number(value[1]))}`, name]
              : [formatMw(Number(value)), name]
          }
        />
        <Legend />
        <Area
          dataKey="band"
          name="Likely range (P10–P90)"
          stroke="none"
          fill={colors.band}
          fillOpacity={0.6}
          isAnimationActive={false}
        />
        <Line
          dataKey="forecast"
          name="Forecast at cutoff"
          stroke={colors.forecast}
          strokeWidth={2.5}
          dot={false}
          isAnimationActive={false}
        />
        {showActual && (
          <Line
            dataKey="actual"
            name="Actual (hindsight)"
            stroke={colors.actual}
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
            isAnimationActive={false}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
