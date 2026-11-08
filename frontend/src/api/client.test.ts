import { afterEach, describe, expect, it, vi } from "vitest";

import { api, ApiError } from "./client";

function mockFetch(status = 200, body: unknown = []) {
  const fn = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fn);
  return fn;
}

const calledUrl = (fn: ReturnType<typeof mockFetch>) => (fn.mock.calls[0] as unknown[])[0] as string;

afterEach(() => vi.unstubAllGlobals());

describe("api.applications filters", () => {
  it.each([
    ["interviewed", "/api/applications?stage=interview"],
    ["advanced", "/api/applications?stage=next_round"],
    ["awaiting", "/api/applications?stage=awaiting"],
    ["rejection", "/api/applications?status=rejection"],
    ["", "/api/applications"],
  ] as const)("%s → %s", async (status, url) => {
    const fetch = mockFetch();
    await api.applications({ status });
    expect(calledUrl(fetch)).toBe(url);
  });

  it("combines status and language", async () => {
    const fetch = mockFetch();
    await api.applications({ status: "ghosted", language: "de" });
    expect(calledUrl(fetch)).toBe("/api/applications?status=ghosted&language=de");
  });
});

describe("errors", () => {
  it("carries the server's code, e.g. pairing_required", async () => {
    mockFetch(401, { detail: "not paired", code: "pairing_required" });
    const err = await api.stats().catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).status).toBe(401);
    expect((err as ApiError).code).toBe("pairing_required");
  });

  it("reports an unreachable server as status 0", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new TypeError("offline"))));
    const err = await api.stats().catch((e: unknown) => e);
    expect((err as ApiError).status).toBe(0);
  });
});
