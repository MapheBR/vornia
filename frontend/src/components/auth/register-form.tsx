"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import type { RegisterRequest, User } from "@/lib/types";

export function RegisterForm() {
  const router = useRouter();
  const [form, setForm] = useState<RegisterRequest>({
    company_name: "",
    full_name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function field(name: keyof RegisterRequest) {
    return {
      value: form[name],
      onChange: (event: React.ChangeEvent<HTMLInputElement>) =>
        setForm((previous) => ({ ...previous, [name]: event.target.value })),
    };
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await apiFetch<User>("/auth/register", {
        method: "POST",
        body: JSON.stringify(form),
      });
      router.push("/colaboradores");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível cadastrar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-sm flex-col gap-4">
      {([
        ["company_name", "Empresa", "text"],
        ["full_name", "Nome completo", "text"],
        ["email", "E-mail", "email"],
        ["password", "Senha", "password"],
      ] as const).map(([name, label, type]) => (
        <div key={name} className="flex flex-col gap-1">
          <label htmlFor={name} className="text-sm font-medium">{label}</label>
          <input
            id={name}
            type={type}
            required
            {...field(name)}
            className="rounded border border-slate-300 px-3 py-2"
          />
        </div>
      ))}
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
      <button
        type="submit"
        disabled={saving}
        className="rounded bg-vornia-azul-profundo px-4 py-2 text-white disabled:opacity-50"
      >
        {saving ? "Cadastrando..." : "Cadastrar"}
      </button>
    </form>
  );
}
