"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import type { User } from "@/lib/types";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await apiFetch<User>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      router.push("/colaboradores");
    } catch {
      setError("Credenciais inválidas");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-sm flex-col gap-4">
      <div className="flex flex-col gap-1">
        <label htmlFor="email" className="text-sm font-medium">
          E-mail
        </label>
        <input
          id="email"
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="rounded-md border border-vornia-borda px-3 py-2 focus:border-vornia-verde-escuro focus:outline-none focus:ring-2 focus:ring-vornia-verde-suave"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label htmlFor="password" className="text-sm font-medium">
          Senha
        </label>
        <input
          id="password"
          type="password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="rounded-md border border-vornia-borda px-3 py-2 focus:border-vornia-verde-escuro focus:outline-none focus:ring-2 focus:ring-vornia-verde-suave"
        />
      </div>
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
      <button
        type="submit"
        disabled={saving}
        className="rounded-md bg-vornia-verde-suave px-4 py-2 font-semibold text-vornia-azul-profundo transition-colors hover:bg-vornia-verde-escuro disabled:opacity-50"
      >
        {saving ? "Entrando..." : "Entrar"}
      </button>
    </form>
  );
}
