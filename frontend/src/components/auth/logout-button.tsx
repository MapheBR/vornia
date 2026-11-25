"use client";

import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";

export function LogoutButton() {
  const router = useRouter();

  async function handleLogout() {
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } finally {
      router.push("/login");
    }
  }

  return (
    <button
      type="button"
      onClick={() => void handleLogout()}
      className="rounded border border-slate-300 px-3 py-1 text-sm"
    >
      Sair
    </button>
  );
}
