import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Accuracy } from "../api/types";
import { formatGw, formatMw, formatShortDay, formatStamp } from "../lib/format";
import { axisProps, colors, gwTick } from "./theme";

export function SeriesChart({ series }: { series: Accuracy["series"] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={series} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={colors.grid} vertical={false} />
        <XAxis
          dataKey="time"
          tickFormatter={(t: string) => formatShortDay(t.slice(0, 10))}
          minTickGap={40}
          {...axisProps}
        />
        <YAxis tickFormatter={gwTick} width={44} {...axisProps} />
        <Tooltip labelFormatter={(label) => formatStamp(String(label))} formatter={(v, n) => [formatMw(Number(v)), n]} />
        <Legend />
        <Line dataKey="forecast" name="Forecast at cutoff" stroke={colors.forecast} dot={false} strokeWidth={1.5} isAnimationActive={false} />
        <Line dataKey="actual" name="Actual" stroke={colors.actual} dot={false} strokeWidth={1.5} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function DailyErrorChart({ byDay }: { byDay: Accuracy["byDay"] }) {
  const data = useMemo(
    () => byDay.map((d) => ({ day: d.deliveryDay, mae: d.summary.mae, bias: d.summary.bias })),
    [byDay],
  );
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={colors.grid} vertical={false} />
        <XAxis dataKey="day" tickFormatter={formatShortDay} minTickGap={24} {...axisProps} />
        <YAxis tickFormatter={gwTick} width={44} {...axisProps} />
        <Tooltip labelFormatter={(label) => formatShortDay(String(label))} formatter={(v, n) => [formatGw(Number(v)), n]} />
        <Legend />
        <ReferenceLine y={0} stroke={colors.muted} />
        <Bar dataKey="mae" name="Mean absolute error" fill={colors.forecast} radius={[3, 3, 0, 0]} isAnimationActive={false} />
        <Line dataKey="bias" name="Bias (forecast − actual)" stroke={colors.accent} strokeWidth={2} dot={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function HourlyErrorChart({ byHour }: { byHour: Accuracy["byHour"] }) {
  const data = useMemo(
    () => byHour.map((h) => ({ hour: `${String(h.hour).padStart(2, "0")}:00`, mae: h.summary.mae, bias: h.summary.bias })),
    [byHour],
  );
  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={colors.grid} vertical={false} />
        <XAxis dataKey="hour" interval={2} {...axisProps} />
        <YAxis tickFormatter={gwTick} width={44} {...axisProps} />
        <Tooltip formatter={(v, n) => [formatGw(Number(v)), n]} />
        <Legend />
        <Bar dataKey="mae" name="Mean absolute error" fill="#5eead4" radius={[3, 3, 0, 0]} isAnimationActive={false} />
        <Line dataKey="bias" name="Bias" stroke={colors.accent} strokeWidth={2} dot={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function HistogramChart({ histogram }: { histogram: Accuracy["histogram"] }) {
  const data = useMemo(
    () => histogram.map((b) => ({ ...b, mid: (b.start + b.end) / 2, label: `${gwTick(b.start)}` })),
    [histogram],
  );
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }} barCategoryGap={1}>
        <CartesianGrid stroke={colors.grid} vertical={false} />
        <XAxis dataKey="mid" tickFormatter={(v: number) => (v / 1000).toFixed(1)} minTickGap={20} {...axisProps} />
        <YAxis width={44} allowDecimals={false} {...axisProps} />
        <Tooltip
          labelFormatter={(_, payload) => {
            const bin = payload?.[0]?.payload as { start: number; end: number } | undefined;
            return bin ? `${formatMw(bin.start)} to ${formatMw(bin.end)}` : "";
          }}
          formatter={(v) => [`${v} hours`, "Count"]}
        />
        <ReferenceLine x={0} stroke={colors.actual} />
        <Bar dataKey="count" isAnimationActive={false}>
          {data.map((bin) => (
            <Cell key={bin.start} fill={bin.mid >= 0 ? colors.over : colors.under} fillOpacity={0.75} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
