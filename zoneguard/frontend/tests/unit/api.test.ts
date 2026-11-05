import { afterEach, describe, expect, it, vi } from "vitest";

import { api, ApiError } from "@/lib/api";

afterEach(() => vi.restoreAllMocks());

describe("api()", () => {
  it("sends the CSRF header and JSON body", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "content-type": "application/json" } }),
    );
    await api("/api/orgs/x/sites", { body: { name: "A" } });
    const [, init] = fetchMock.mock.calls[0];
    expect((init!.headers as Record<string, string>)["X-Requested-With"]).toBe("zoneguard");
    expect(init!.method).toBe("POST");
    expect(init!.credentials).toBe("same-origin");
  });

  it("turns FastAPI validation errors into readable messages", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      new Response(JSON.stringify({ detail: [{ loc: ["body", "email"], msg: "value is not a valid email address" }] }), {
        status: 422,
        headers: { "content-type": "application/json" },
      }),
    );
    await expect(api("/api/auth/register", { body: {} })).rejects.toThrow("email: value is not a valid email address");
    await expect(api("/api/auth/register", { body: {} })).rejects.toBeInstanceOf(ApiError);
  });
});
