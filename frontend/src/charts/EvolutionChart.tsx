import { useMemo } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Vintages } from "../api/types";
import { formatHour, formatMw, formatStamp } from "../lib/format";
import { axisProps, colors, gwTick } from "./theme";

interface Props {
  vintages: Vintages;
}

export function EvolutionChart({ vintages }: Props) {
  const { rows, keys } = useMemo(() => {
    const byTime = new Map<string, Record<string, number | string>>();
    const ensure = (time: string) => {
      let row = byTime.get(time);
      if (!row) {
        row = { time };
        byTime.set(time, row);
      }
      return row;
    };
    for (const point of vintages.actuals) ensure(point.time).actual = point.generation;
    const keys = vintages.vintages.map((v) => ({ key: v.publishTime, usable: v.usableForDecision }));
    for (const vintage of vintages.vintages) {
      for (const point of vintage.points) ensure(point.time)[vintage.publishTime] = point.generation;
    }
    const rows = [...byTime.values()].sort((a, b) => String(a.time).localeCompare(String(b.time)));
    return { rows, keys };
  }, [vintages]);

  const lastUsable = [...keys].reverse().find((k) => k.usable)?.key;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={colors.grid} vertical={false} />
        <XAxis dataKey="time" tickFormatter={formatHour} interval={2} {...axisProps} />
        <YAxis tickFormatter={gwTick} width={44} {...axisProps} />
        <Tooltip
          labelFormatter={(label) => `Hour starting ${formatHour(String(label))}`}
          formatter={(value, name) => [formatMw(Number(value)), name === "actual" ? "Actual" : `Published ${formatStamp(String(name))}`]}
          itemSorter={(item) => String(item.name)}
        />
        {keys.map(({ key, usable }) => (
          <Line
            key={key}
            dataKey={key}
            stroke={key === lastUsable ? colors.forecast : usable ? "#5eead4" : colors.muted}
            strokeWidth={key === lastUsable ? 3 : 1.25}
            strokeDasharray={usable ? undefined : "3 3"}
            strokeOpacity={usable ? 1 : 0.7}
            dot={false}
            isAnimationActive={false}
            connectNulls
          />
        ))}
        <Line dataKey="actual" stroke={colors.actual} strokeWidth={2.5} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
