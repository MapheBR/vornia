import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const ROOT = path.resolve(process.cwd(), "..");

describe("assets de branding no runtime", () => {
  it("copia a pasta public do builder para a imagem final", () => {
    const dockerfile = readFileSync(
      path.join(ROOT, "docker", "Dockerfile.frontend"),
      "utf8",
    );

    expect(dockerfile).toContain("COPY --from=builder /app/public ./public");
  });

  it("mantem a logo versionada em frontend/public", () => {
    expect(existsSync(path.join(process.cwd(), "public", "logo.png"))).toBe(true);
  });
});
