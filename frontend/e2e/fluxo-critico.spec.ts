import { expect, test } from "@playwright/test";

test.describe("fluxo crítico do Vornia", () => {
  test("registro, criação de colaborador, settings e logout", async ({ page }) => {
    const suffix = Date.now().toString(36);

    await page.goto("/register");
    await page.getByLabel("Empresa").fill(`Acme ${suffix}`);
    await page.getByLabel("Nome completo").fill("Admin Teste");
    await page.getByLabel("E-mail").fill(`admin-${suffix}@acme.example.com`);
    await page.getByLabel("Senha").fill("strong-password");
    await page.getByRole("button", { name: /cadastrar/i }).click();

    await expect(page).toHaveURL(/\/colaboradores/);

    await page.getByRole("button", { name: /novo colaborador/i }).click();
    await page.getByLabel("Nome", { exact: true }).fill("Colaborador E2E");
    await page.getByRole("button", { name: /salvar/i }).click();
    await expect(page.getByText("Colaborador E2E")).toBeVisible();

    await page.goto("/configuracoes");
    await expect(page.getByText("America/Sao_Paulo")).toBeVisible();
    await page.getByLabel("Valor (JSON)").fill('"Europe/London"');
    await page.getByRole("button", { name: /salvar/i }).click();
    await expect(page.getByText("Europe/London")).toBeVisible();

    await page.getByRole("button", { name: /restaurar padrão/i }).first().click();
    await expect(page.getByText("America/Sao_Paulo")).toBeVisible();

    await page.goto("/colaboradores");
    await page.getByRole("button", { name: /sair/i }).click();
    await expect(page).toHaveURL(/\/login/);

    const errors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    expect(errors).toEqual([]);
  });
});
