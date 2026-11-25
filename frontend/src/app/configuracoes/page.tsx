import { SettingsManager } from "@/components/settings/settings-manager";

export default function ConfiguracoesPage() {
  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Configurações</h1>
      <SettingsManager />
    </main>
  );
}
