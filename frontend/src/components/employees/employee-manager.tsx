"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { useDebounce } from "@/lib/hooks";
import type { Employee, EmployeePayload, Paginated } from "@/lib/types";

type FormState = {
  name: string;
  cpf: string;
  registration: string;
  job_title: string;
  department: string;
};

const EMPTY_FORM: FormState = {
  name: "",
  cpf: "",
  registration: "",
  job_title: "",
  department: "",
};

function fromEmployee(employee: Employee): FormState {
  return {
    name: employee.name,
    cpf: employee.cpf ?? "",
    registration: employee.registration ?? "",
    job_title: employee.job_title ?? "",
    department: employee.department ?? "",
  };
}

export function EmployeeManager() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [active, setActive] = useState<boolean | undefined>(undefined);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debouncedSearch = useDebounce(search, 300);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({ page: String(page), per_page: "20" });
    if (debouncedSearch) params.set("search", debouncedSearch);
    if (active !== undefined) params.set("active", String(active));
    try {
      const response = await apiFetch<Paginated<Employee>>(
        `/employees?${params.toString()}`,
      );
      setEmployees(response.data);
      setTotal(response.meta.total);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Erro ao carregar");
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch, active]);

  useEffect(() => {
    void load();
  }, [load]);

  function field(name: keyof FormState) {
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
    const payload: EmployeePayload = {
      name: form.name.trim(),
      registration: form.registration.trim() || null,
      cpf: form.cpf.trim() || null,
      job_title: form.job_title.trim() || null,
      department: form.department.trim() || null,
    };
    try {
      if (editingId) {
        await apiFetch(`/employees/${editingId}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
      } else {
        await apiFetch("/employees", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }
      setForm(EMPTY_FORM);
      setEditingId(null);
      setShowForm(false);
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Desativar este colaborador?")) return;
    try {
      await apiFetch(`/employees/${id}`, { method: "DELETE" });
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Erro ao desativar");
    }
  }

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <input
          type="search"
          placeholder="Buscar colaborador"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
          className="rounded border border-slate-300 px-3 py-2"
        />
        <select
          aria-label="Filtrar por situação"
          value={active === undefined ? "" : String(active)}
          onChange={(event) =>
            setActive(event.target.value === "" ? undefined : event.target.value === "true")
          }
          className="rounded border border-slate-300 px-3 py-2"
        >
          <option value="">Todos</option>
          <option value="true">Ativos</option>
          <option value="false">Inativos</option>
        </select>
        <button
          type="button"
          onClick={() => {
            setForm(EMPTY_FORM);
            setEditingId(null);
            setShowForm(true);
          }}
          className="rounded bg-vornia-azul-profundo px-4 py-2 text-white"
        >
          Novo colaborador
        </button>
      </div>

      {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
      {loading && <p className="text-sm text-slate-500">Carregando...</p>}

      {showForm && (
        <form onSubmit={handleSubmit} className="grid gap-3 rounded border p-4 sm:grid-cols-2">
          {([
            ["name", "Nome"],
            ["cpf", "CPF"],
            ["registration", "Matrícula"],
            ["job_title", "Cargo"],
            ["department", "Departamento"],
          ] as const).map(([name, label]) => (
            <label key={name} className="flex flex-col gap-1 text-sm">
              {label}
              <input
                {...field(name)}
                className="rounded border border-slate-300 px-3 py-2"
              />
            </label>
          ))}
          <button
            type="submit"
            disabled={saving}
            className="rounded bg-vornia-verde-suave px-4 py-2 text-vornia-azul-profundo disabled:opacity-50"
          >
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </form>
      )}

      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b">
            <th className="py-2">Nome</th>
            <th>Matrícula</th>
            <th>Cargo</th>
            <th>Departamento</th>
            <th>CPF</th>
            <th>Situação</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {employees.map((employee) => (
            <tr key={employee.id} className="border-b">
              <td className="py-2">{employee.name}</td>
              <td>{employee.registration ?? "—"}</td>
              <td>{employee.job_title ?? "—"}</td>
              <td>{employee.department ?? "—"}</td>
              <td>{employee.cpf ?? "—"}</td>
              <td>{employee.is_active ? "Ativo" : "Inativo"}</td>
              <td className="flex gap-2 py-2">
                <button
                  type="button"
                  onClick={() => {
                    setForm(fromEmployee(employee));
                    setEditingId(employee.id);
                    setShowForm(true);
                  }}
                  className="text-blue-700"
                >
                  Editar
                </button>
                <button
                  type="button"
                  onClick={() => void handleDelete(employee.id)}
                  className="text-red-700"
                >
                  Desativar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="text-sm text-slate-500">{total} colaborador(es)</p>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => setPage((previous) => Math.max(1, previous - 1))}
          className="rounded border px-3 py-1 disabled:opacity-50"
        >
          Anterior
        </button>
        <span className="px-2 py-1 text-sm">Página {page}</span>
        <button
          type="button"
          onClick={() => setPage((previous) => previous + 1)}
          className="rounded border px-3 py-1"
        >
          Próxima
        </button>
      </div>
    </section>
  );
}
