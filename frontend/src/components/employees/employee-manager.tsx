"use client";

import { useCallback, useEffect, useState } from "react";

import { employeesApi } from "@/lib/api";
import type { Employee, EmployeePayload } from "@/lib/types";

interface FormState {
  name: string;
  registration: string;
  jobTitle: string;
  department: string;
  cpf: string;
  pis: string;
  controlId: string;
  hiredAt: string;
}

const EMPTY_FORM: FormState = {
  name: "",
  registration: "",
  jobTitle: "",
  department: "",
  cpf: "",
  pis: "",
  controlId: "",
  hiredAt: "",
};

function fromEmployee(employee: Employee): FormState {
  return {
    name: employee.name,
    registration: employee.registration ?? "",
    jobTitle: employee.job_title ?? "",
    department: employee.department ?? "",
    cpf: employee.cpf ?? "",
    pis: employee.pis ?? "",
    controlId: employee.control_id === null ? "" : String(employee.control_id),
    hiredAt: employee.hired_at ?? "",
  };
}

function toPayload(form: FormState): EmployeePayload {
  return {
    name: form.name.trim(),
    registration: form.registration.trim() || null,
    job_title: form.jobTitle.trim() || null,
    department: form.department.trim() || null,
    cpf: form.cpf.trim() || null,
    pis: form.pis.trim() || null,
    control_id: form.controlId.trim() ? Number(form.controlId) : null,
    hired_at: form.hiredAt || null,
  };
}

export function EmployeeManager() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setEmployees(await employeesApi.list());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível carregar os colaboradores");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  function updateField(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (form.name.trim().length === 0) {
      setError("Informe o nome do colaborador");
      return;
    }
    if (form.controlId.trim() && !Number.isInteger(Number(form.controlId))) {
      setError("O ID do relógio de ponto deve ser um número inteiro");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const payload = toPayload(form);
      if (editingId) {
        await employeesApi.update(editingId, payload);
      } else {
        await employeesApi.create(payload);
      }
      setForm(EMPTY_FORM);
      setEditingId(null);
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível salvar o colaborador");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(employee: Employee) {
    if (!window.confirm(`Excluir ${employee.name}?`)) return;
    setError(null);
    try {
      await employeesApi.remove(employee.id);
      if (editingId === employee.id) {
        setForm(EMPTY_FORM);
        setEditingId(null);
      }
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível excluir o colaborador");
    }
  }

  return (
    <main className="mx-auto max-w-6xl p-8">
      <h1 className="text-3xl font-bold text-vornia-azul-profundo">Colaboradores</h1>
      <p className="mt-2 text-vornia-azul-profundo/80">
        Cadastre e mantenha os colaboradores da sua empresa.
      </p>

      <div aria-live="polite" className="mt-4 min-h-6">
        {error && <p className="rounded bg-red-50 p-3 text-sm text-red-800">{error}</p>}
      </div>

      <form
        onSubmit={handleSubmit}
        className="mt-4 grid gap-4 rounded-lg bg-white p-6 shadow-sm md:grid-cols-2"
      >
        <label className="flex flex-col gap-1 text-sm text-vornia-azul-profundo">
          Nome *
          <input
            required
            value={form.name}
            onChange={(event) => updateField("name", event.target.value)}
            className="rounded border border-vornia-azul-profundo/30 p-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-vornia-azul-profundo">
          Matrícula
          <input
            value={form.registration}
            onChange={(event) => updateField("registration", event.target.value)}
            className="rounded border border-vornia-azul-profundo/30 p-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-vornia-azul-profundo">
          Cargo
          <input
            value={form.jobTitle}
            onChange={(event) => updateField("jobTitle", event.target.value)}
            className="rounded border border-vornia-azul-profundo/30 p-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-vornia-azul-profundo">
          Departamento
          <input
            value={form.department}
            onChange={(event) => updateField("department", event.target.value)}
            className="rounded border border-vornia-azul-profundo/30 p-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-vornia-azul-profundo">
          ID do relógio
          <input
            inputMode="numeric"
            value={form.controlId}
            onChange={(event) => updateField("controlId", event.target.value)}
            className="rounded border border-vornia-azul-profundo/30 p-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-vornia-azul-profundo">
          Admissão
          <input
            type="date"
            value={form.hiredAt}
            onChange={(event) => updateField("hiredAt", event.target.value)}
            className="rounded border border-vornia-azul-profundo/30 p-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-vornia-azul-profundo">
          CPF
          <input
            value={form.cpf}
            onChange={(event) => updateField("cpf", event.target.value)}
            className="rounded border border-vornia-azul-profundo/30 p-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-vornia-azul-profundo">
          PIS
          <input
            value={form.pis}
            onChange={(event) => updateField("pis", event.target.value)}
            className="rounded border border-vornia-azul-profundo/30 p-2"
          />
        </label>
        <div className="flex items-end gap-2 md:col-span-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded bg-vornia-azul-profundo px-4 py-2 text-white disabled:opacity-60"
          >
            {editingId ? "Salvar alterações" : "Adicionar colaborador"}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={() => {
                setForm(EMPTY_FORM);
                setEditingId(null);
              }}
              className="rounded border border-vornia-azul-profundo/30 px-4 py-2 text-vornia-azul-profundo"
            >
              Cancelar
            </button>
          )}
        </div>
      </form>

      <section className="mt-8 overflow-x-auto rounded-lg bg-white shadow-sm" aria-label="Lista de colaboradores">
        {loading ? (
          <p className="p-6 text-vornia-azul-profundo/70">Carregando…</p>
        ) : employees.length === 0 ? (
          <p className="p-6 text-vornia-azul-profundo/70">Nenhum colaborador cadastrado.</p>
        ) : (
          <table className="w-full text-left text-sm text-vornia-azul-profundo">
            <thead className="bg-vornia-cinza-claro">
              <tr>
                <th scope="col" className="p-3">Nome</th>
                <th scope="col" className="p-3">Matrícula</th>
                <th scope="col" className="p-3">Cargo</th>
                <th scope="col" className="p-3">Departamento</th>
                <th scope="col" className="p-3">Ações</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((employee) => (
                <tr key={employee.id} className="border-t border-vornia-cinza-claro">
                  <td className="p-3">{employee.name}</td>
                  <td className="p-3">{employee.registration ?? "—"}</td>
                  <td className="p-3">{employee.job_title ?? "—"}</td>
                  <td className="p-3">{employee.department ?? "—"}</td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setForm(fromEmployee(employee));
                          setEditingId(employee.id);
                        }}
                        className="rounded border border-vornia-azul-profundo/30 px-2 py-1"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleDelete(employee)}
                        className="rounded border border-red-300 px-2 py-1 text-red-700"
                      >
                        Excluir
                      </button>
                    </div>
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
