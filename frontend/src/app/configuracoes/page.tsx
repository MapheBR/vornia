import { SettingsManager } from "@/components/settings/settings-manager";
import { LogoutButton } from "@/components/auth/logout-button";
import { AppHeader } from "@/components/layout/app-header";

export default function ConfiguracoesPage() {
  return (
    <div className="min-h-screen bg-vornia-cinza-claro">
      <AppHeader />
      <main className="mx-auto max-w-4xl p-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-vornia-azul-profundo">Configurações</h1>
          <LogoutButton />
        </div>
        <SettingsManager />
      </main>
    </div>
  );
}
