const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export function buildUrl(path: string, params: Record<string, string | undefined> = {}): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") query.set(key, value);
  }
  const suffix = query.toString();
  return `${API_BASE}${path}${suffix ? `?${suffix}` : ""}`;
}

export async function getJson<T>(
  path: string,
  params: Record<string, string | undefined> = {},
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(buildUrl(path, params), { signal, headers: { Accept: "application/json" } });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const error = body?.error ?? {};
    throw new ApiError(response.status, error.code ?? "http_error", error.message ?? response.statusText);
  }
  return (await response.json()) as T;
}
