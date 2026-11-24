import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold text-vornia-azul-profundo">Vornia</h1>
      <p className="mt-4 text-lg text-vornia-azul-profundo/80">Workforce Intelligence</p>
      <nav aria-label="Navegação principal" className="mt-8 flex flex-wrap justify-center gap-4">
        <Button asChild variant="secondary">
          <Link href="/colaboradores">Colaboradores</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/configuracoes">Configurações</Link>
        </Button>
      </nav>
    </main>
  );
}
