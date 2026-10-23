export const colors = {
  forecast: "#0f766e",
  band: "#99f6e4",
  actual: "#1e293b",
  over: "#dc2626",
  under: "#2563eb",
  muted: "#94a3b8",
  grid: "#e2e8f0",
  accent: "#f59e0b",
} as const;

export const axisProps = {
  stroke: colors.muted,
  tick: { fontSize: 12, fill: "#64748b" },
  tickLine: false,
} as const;

export const gwTick = (value: number): string => `${(value / 1000).toFixed(0)}`;
