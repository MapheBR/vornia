import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-vornia-azul-profundo">Vornia</h1>
        <p className="mt-4 text-lg text-vornia-azul-profundo/80">
          Workforce Intelligence
        </p>
      </div>
      <nav className="flex flex-wrap justify-center gap-4">
        <Link href="/colaboradores">
          <Button>Colaboradores</Button>
        </Link>
        <Link href="/configuracoes">
          <Button variant="secondary">Configurações</Button>
        </Link>
        <Link href="/login">
          <Button variant="secondary">Entrar</Button>
        </Link>
      </nav>
    </main>
  );
}
