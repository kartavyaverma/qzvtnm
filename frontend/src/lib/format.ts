const TIMEZONE = "Europe/London";

const hourFormat = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: TIMEZONE });
const dayFormat = new Intl.DateTimeFormat("en-GB", {
  weekday: "short",
  day: "numeric",
  month: "short",
  timeZone: TIMEZONE,
});
const shortDayFormat = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", timeZone: TIMEZONE });
const stampFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: TIMEZONE,
});

export function formatMw(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "–";
  return `${value.toLocaleString("en-GB", { maximumFractionDigits: digits })} MW`;
}

export function formatGw(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "–";
  return `${(value / 1000).toLocaleString("en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} GW`;
}

export function formatSignedGw(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "–";
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${formatGw(Math.abs(value))}`;
}

export function formatGwh(mwh: number | null | undefined): string {
  if (mwh === null || mwh === undefined || Number.isNaN(mwh)) return "–";
  return `${(mwh / 1000).toLocaleString("en-GB", { maximumFractionDigits: 1 })} GWh`;
}

export function formatPct(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "–";
  return `${value.toFixed(digits)}%`;
}

export const formatHour = (iso: string): string => hourFormat.format(new Date(iso));
export const formatDay = (isoDate: string): string => dayFormat.format(new Date(`${isoDate}T12:00:00Z`));
export const formatShortDay = (isoDate: string): string => shortDayFormat.format(new Date(`${isoDate}T12:00:00Z`));
export const formatStamp = (iso: string): string => stampFormat.format(new Date(iso));

export function shiftDay(days: string[], current: string, step: number): string | undefined {
  const index = days.indexOf(current);
  if (index === -1) return undefined;
  return days[index + step];
}
