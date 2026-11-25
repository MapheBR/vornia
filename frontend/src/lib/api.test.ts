import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch, ApiError, setRefreshHandler } from "@/lib/api";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
  setRefreshHandler(null);
});

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("apiFetch", () => {
  it("usa credenciais (cookies HttpOnly) e caminho relativo /api/v1", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    globalThis.fetch = fetchMock;

    await apiFetch("/auth/me");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/me"),
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("não aponta para localhost:8000 (mesma origem via Caddy)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    globalThis.fetch = fetchMock;

    await apiFetch("/employees");

    expect(fetchMock.mock.calls[0]?.[0]).not.toContain("localhost:8000");
  });

  it("lança ApiError com status e detalhe em respostas de erro", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      jsonResponse({ detail: "Chave desconhecida" }, 422),
    );

    await expect(apiFetch("/settings/unknown")).rejects.toMatchObject({
      status: 422,
      detail: "Chave desconhecida",
    });
    expect(ApiError).toBeDefined();
  });

  it("renova o token (POST /auth/refresh) e repete a requisição após 401", async () => {
    setRefreshHandler(vi.fn().mockResolvedValue(true));
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ detail: "Unauthorized" }, 401))
      .mockResolvedValue(jsonResponse({ ok: true }));
    globalThis.fetch = fetchMock;

    await apiFetch("/employees");

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/api/v1/employees");
    expect(fetchMock.mock.calls[1]?.[0]).toContain("/api/v1/employees");
  });

  it("não repete infinitamente se o refresh falhar", async () => {
    setRefreshHandler(vi.fn().mockResolvedValue(false));
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: "Unauthorized" }, 401));
    globalThis.fetch = fetchMock;

    await expect(apiFetch("/employees")).rejects.toBeInstanceOf(ApiError);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
