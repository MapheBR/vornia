"use client";

import { apiFetch, setRefreshHandler } from "@/lib/api";
import type { User } from "@/lib/types";

/** Sonda a sessão; em 401 tenta renovar via /auth/refresh. */
export async function fetchCurrentUser(): Promise<User | null> {
  setRefreshHandler(async () => {
    try {
      await apiFetch("/auth/refresh", { method: "POST" });
      return true;
    } catch {
      return false;
    }
  });

  try {
    return await apiFetch<User>("/auth/me");
  } catch {
    return null;
  }
}
