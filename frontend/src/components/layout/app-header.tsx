import Link from "next/link";

import { BrandLogo } from "@/components/brand/logo";

const LINK_CLASS =
  "text-sm font-medium text-vornia-branco transition-colors hover:text-vornia-verde-suave";

/** Cabeçalho comum às telas autenticadas. */
export function AppHeader() {
  return (
    <header
      data-testid="app-header"
      className="border-b-2 border-vornia-verde-suave bg-vornia-azul-profundo"
    >
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-3">
        <Link href="/dashboard" aria-label="Vornia — início">
          <BrandLogo width={150} />
        </Link>
        <nav aria-label="Navegação principal" className="flex flex-wrap gap-4">
          <Link href="/dashboard" className={LINK_CLASS}>Dashboard</Link>
          <Link href="/colaboradores" className={LINK_CLASS}>Colaboradores</Link>
          <Link href="/configuracoes" className={LINK_CLASS}>Configurações</Link>
        </nav>
      </div>
    </header>
  );
}
