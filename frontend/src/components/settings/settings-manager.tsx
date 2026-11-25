"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { SETTINGS_KEYS, type SettingsKey } from "@/lib/types";

export function SettingsManager() {
  const [settings, setSettings] = useState<Record<string, unknown>>({});
  const [key, setKey] = useState<SettingsKey>("timezone");
  const [value, setValue] = useState('"America/Sao_Paulo"');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch<{ data: Record<string, unknown> }>("/settings");
      setSettings(response.data);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Erro ao carregar");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSave(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    let parsed: unknown;
    try {
      parsed = JSON.parse(value);
    } catch {
      setError("O valor deve ser um JSON válido");
      return;
    }

    setSaving(true);
    try {
      await apiFetch(`/settings/${key}`, {
        method: "PUT",
        body: JSON.stringify({ value: parsed }),
      });
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(selected: string) {
    setError(null);
    try {
      await apiFetch(`/settings/${selected}`, { method: "DELETE" });
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Erro ao remover");
    }
  }

  return (
    <section className="flex flex-col gap-4">
      {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
      {loading && <p className="text-sm text-slate-500">Carregando...</p>}

      <form onSubmit={handleSave} className="grid gap-3 rounded border p-4 sm:grid-cols-3">
        <label className="flex flex-col gap-1 text-sm">
          Chave
          <select
            value={key}
            onChange={(event) => setKey(event.target.value as SettingsKey)}
            className="rounded border border-slate-300 px-3 py-2"
          >
            {SETTINGS_KEYS.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Valor (JSON)
          <input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            className="rounded border border-slate-300 px-3 py-2"
          />
        </label>
        <button
          type="submit"
          disabled={saving}
          className="self-end rounded bg-vornia-azul-profundo px-4 py-2 text-white disabled:opacity-50"
        >
          {saving ? "Salvando..." : "Salvar"}
        </button>
      </form>

      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b">
            <th className="py-2">Chave</th>
            <th>Valor efetivo</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(settings).map(([settingKey, settingValue]) => (
            <tr key={settingKey} className="border-b">
              <td className="py-2">{settingKey}</td>
              <td>{JSON.stringify(settingValue)}</td>
              <td>
                <button
                  type="button"
                  onClick={() => void handleDelete(settingKey)}
                  className="text-red-700"
                >
                  Restaurar padrão
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
