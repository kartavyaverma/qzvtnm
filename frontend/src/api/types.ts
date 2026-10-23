export interface Summary {
  count: number;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  nmaePct: number | null;
  p50Error: number | null;
  p90Error: number | null;
  p95AbsError: number | null;
  maxOverForecast: number | null;
  maxUnderForecast: number | null;
  overForecastSharePct: number | null;
  meanActual: number | null;
  meanForecast: number | null;
}

export interface CutoffPreset {
  label: string;
  cutoff: string;
  description: string;
}

export interface Meta {
  timezone: string;
  decisionWindowStart: string;
  decisionWindowEnd: string;
  deliveryDays: string[];
  defaultCutoff: string;
  cutoffPresets: CutoffPreset[];
  publishScheduleUtc: string[];
  sources: Record<string, string>;
  errorConvention: string;
}

export interface DecisionPoint {
  time: string;
  forecast: number;
  actual: number;
  error: number;
  publishTime: string;
  horizonHours: number;
  low: number | null;
  high: number | null;
}

export interface Decision {
  deliveryDay: string;
  decisionDay: string;
  cutoff: string;
  cutoffUtc: string;
  forecastPublishTimes: string[];
  historyDays: number;
  bandAvailable: boolean;
  summary: Summary;
  energy: { forecastMwh: number; actualMwh: number; conservativeMwh: number | null };
  points: DecisionPoint[];
}

export interface Accuracy {
  cutoff: string;
  deliveryStart: string;
  deliveryEnd: string;
  summary: Summary;
  errorQuantiles: Record<string, number>;
  byDay: { deliveryDay: string; summary: Summary }[];
  byHour: { hour: number; summary: Summary }[];
  histogram: { start: number; end: number; count: number }[];
  series: { time: string; forecast: number; actual: number }[];
}

export interface Horizon {
  bucketHours: number;
  decisionHorizonMin: number | null;
  decisionHorizonMax: number | null;
  buckets: { startHours: number; endHours: number; summary: Summary }[];
}

export interface Vintages {
  deliveryDay: string;
  cutoff: string;
  actuals: { time: string; generation: number }[];
  vintages: { publishTime: string; usableForDecision: boolean; points: { time: string; generation: number }[] }[];
}
