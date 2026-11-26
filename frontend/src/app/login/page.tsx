import { BrandLogo } from "@/components/brand/logo";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-vornia-azul-profundo p-8">
      <div
        data-testid="login-card"
        className="w-full max-w-md rounded-xl border-2 border-vornia-verde-suave bg-vornia-branco p-8 shadow-lg"
      >
        <div className="mb-8 flex flex-col items-center gap-4 text-center">
          <BrandLogo width={240} />
          <h1 className="text-2xl font-bold text-vornia-azul-profundo">
            Entrar no Vornia
          </h1>
          <p className="text-sm text-vornia-azul-profundo/70">
            Gestão de ponto, jornadas e banco de horas.
          </p>
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
