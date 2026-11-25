import { describe, expect, it } from "vitest";

import { readFileSync } from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "..");
const CONFIG = readFileSync(path.join(ROOT, "docker-compose.yml"), "utf-8");
const CADDYFILE = readFileSync(path.join(ROOT, "docker", "Caddyfile"), "utf-8");

describe("configuração de rede (same-origin via Caddy)", () => {
  it("Caddyfile encaminha /api/* para o FastAPI na porta 8000", () => {
    expect(CADDYFILE).toMatch(/handle \/api\/\*/);
    expect(CADDYFILE).toMatch(/reverse_proxy backend:8000/);
  });

  it("Caddyfile encaminha o restante para o Next.js na porta 3000", () => {
    expect(CADDYFILE).toMatch(/handle \{/);
    expect(CADDYFILE).toMatch(/reverse_proxy frontend:3000/);
  });

  it("docker-compose publica o Caddy em localhost:8080", () => {
    expect(CONFIG).toMatch(/"8080:80"/);
  });

  it("frontend usa a mesma origem do Caddy por padrão", () => {
    expect(CONFIG).toMatch(/NEXT_PUBLIC_API_URL: \$\{NEXT_PUBLIC_API_URL:-\/?/);
  });
});
