"use client";

import { useEffect, useState } from "react";

import Link from "next/link";

import { LogoutButton } from "@/components/auth/logout-button";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

interface Summary {
  total_employees: number;
  hours_worked: number;
  inconsistencies: number;
  pending_journeys: number;
}

export function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Summary>("/dashboard/summary")
      .then(setSummary)
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : "Erro ao carregar"),
      );
  }, []);

  return (
    <section className="flex flex-col gap-6">
      <div className="flex justify-end">
        <LogoutButton />
      </div>
      {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card title="Colaboradores" value={summary?.total_employees ?? "—"} />
        <Card title="Horas trabalhadas" value={summary?.hours_worked ?? "—"} />
        <Card title="Inconsistências" value={summary?.inconsistencies ?? "—"} />
        <Card title="Jornadas pendentes" value={summary?.pending_journeys ?? "—"} />
      </div>
      <Link href="/colaboradores">
        <Button>Gerenciar colaboradores</Button>
      </Link>
    </section>
  );
}

function Card({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="rounded border p-4">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
