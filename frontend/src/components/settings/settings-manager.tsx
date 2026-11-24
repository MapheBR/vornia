"use client";

import { useCallback, useEffect, useState } from "react";

import { settingsApi } from "@/lib/api";

export function SettingsManager() {
  const [settings, setSettings] = useState<Record<string, unknown>>({});
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setSettings(await settingsApi.list());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível carregar as configurações");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSave(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!key.trim()) {
      setError("Informe a chave da configuração");
      return;
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(value);
    } catch {
      setError("O valor deve ser um JSON válido (ex.: \"America/Sao_Paulo\" ou 8.8)");
      return;
    }

    setError(null);
    try {
      await settingsApi.put(key.trim(), parsed);
      setKey("");
      setValue("");
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível salvar a configuração");
    }
  }

  async function handleDelete(settingKey: string) {
    if (!window.confirm(`Excluir a configuração ${settingKey}?`)) return;
    setError(null);
    try {
      await settingsApi.remove(settingKey);
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível excluir a configuração");
    }
  }

  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="text-3xl font-bold text-vornia-azul-profundo">Configurações</h1>
      <p className="mt-2 text-vornia-azul-profundo/80">
        Parâmetros aplicados apenas à sua empresa.
      </p>

      <div aria-live="polite" className="mt-4 min-h-6">
        {error && <p className="rounded bg-red-50 p-3 text-sm text-red-800">{error}</p>}
      </div>

      <form onSubmit={handleSave} className="mt-4 flex flex-wrap items-end gap-4 rounded-lg bg-white p-6 shadow-sm">
        <label className="flex flex-col gap-1 text-sm text-vornia-azul-profundo">
          Chave *
          <input
            required
            value={key}
            onChange={(event) => setKey(event.target.value)}
            className="rounded border border-vornia-azul-profundo/30 p-2"
          />
        </label>
        <label className="flex flex-1 flex-col gap-1 text-sm text-vornia-azul-profundo">
          Valor (JSON) *
          <input
            required
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder={'\"America/Sao_Paulo\"'}
            className="rounded border border-vornia-azul-profundo/30 p-2"
          />
        </label>
        <button
          type="submit"
          className="rounded bg-vornia-azul-profundo px-4 py-2 text-white"
        >
          Salvar
        </button>
      </form>

      <section className="mt-8 overflow-x-auto rounded-lg bg-white shadow-sm" aria-label="Lista de configurações">
        {loading ? (
          <p className="p-6 text-vornia-azul-profundo/70">Carregando…</p>
        ) : Object.keys(settings).length === 0 ? (
          <p className="p-6 text-vornia-azul-profundo/70">Nenhuma configuração cadastrada.</p>
        ) : (
          <table className="w-full text-left text-sm text-vornia-azul-profundo">
            <thead className="bg-vornia-cinza-claro">
              <tr>
                <th scope="col" className="p-3">Chave</th>
                <th scope="col" className="p-3">Valor</th>
                <th scope="col" className="p-3">Ações</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(settings).map(([settingKey, settingValue]) => (
                <tr key={settingKey} className="border-t border-vornia-cinza-claro">
                  <td className="p-3">{settingKey}</td>
                  <td className="p-3">{JSON.stringify(settingValue)}</td>
                  <td className="p-3">
                    <button
                      type="button"
                      onClick={() => void handleDelete(settingKey)}
                      className="rounded border border-red-300 px-2 py-1 text-red-700"
                    >
                      Excluir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}
