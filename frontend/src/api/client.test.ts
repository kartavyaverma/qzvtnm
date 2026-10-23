import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, buildUrl, getJson } from "./client";

afterEach(() => vi.unstubAllGlobals());

describe("buildUrl", () => {
  it("adds only defined parameters", () => {
    expect(buildUrl("/decision", { day: "2026-01-15", cutoff: undefined })).toBe("/api/v1/decision?day=2026-01-15");
    expect(buildUrl("/meta")).toBe("/api/v1/meta");
  });
});

describe("getJson", () => {
  it("returns parsed JSON on success", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: 1 }), { status: 200 })));
    await expect(getJson("/meta")).resolves.toEqual({ ok: 1 });
  });

  it("surfaces structured API errors", async () => {
    const body = { error: { code: "not_found", message: "delivery day must be between" } };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status: 404 })));
    const error = await getJson("/decision").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, code: "not_found" });
  });

  it("handles non-JSON error bodies", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("oops", { status: 502, statusText: "Bad Gateway" })));
    await expect(getJson("/meta")).rejects.toMatchObject({ status: 502, code: "http_error" });
  });
});
