import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "Vornia — Workforce Intelligence",
  description: "Gestão de ponto eletrônico, jornadas e banco de horas.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="antialiased">{children}</body>
    </html>
  );
}
