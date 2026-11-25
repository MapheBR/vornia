/*
 * Cliente HTTP da API Vornia.
 *
 * Todas as chamadas usam `credentials: "include"` para enviar os cookies HttpOnly
 * (token de acesso e refresh) e apontam para caminhos relativos `/api/v1/...` —
 * em desenvolvimento o Caddy faz proxy same-origin em localhost:8080.
 */

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

type RefreshHandler = () => Promise<boolean>;

let refreshHandler: RefreshHandler | null = null;

export function setRefreshHandler(handler: RefreshHandler | null): void {
  refreshHandler = handler;
}

export function apiUrl(path: string): string {
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}/api/v1${suffix}`;
}

export async function apiFetch<T = unknown>(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    credentials: "include",
    headers: {
      "content-type": "application/json",
      ...init.headers,
    },
  });

  if (response.status === 401 && retry && refreshHandler !== null) {
    const refreshed = await refreshHandler();
    if (refreshed) {
      return apiFetch<T>(path, init, false);
    }
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new ApiError(response.status, body.detail ?? "Erro na requisição");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
