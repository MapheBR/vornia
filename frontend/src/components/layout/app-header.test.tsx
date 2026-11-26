import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppHeader } from "@/components/layout/app-header";

describe("AppHeader", () => {
  it("mostra a logo e os links de navegacao", () => {
    render(<AppHeader />);

    expect(screen.getByRole("img", { name: /vornia/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /dashboard/i })).toHaveAttribute(
      "href",
      "/dashboard",
    );
    expect(screen.getByRole("link", { name: /colaboradores/i })).toHaveAttribute(
      "href",
      "/colaboradores",
    );
    expect(screen.getByRole("link", { name: /configurações/i })).toHaveAttribute(
      "href",
      "/configuracoes",
    );
  });

  it("usa a paleta Vornia com acento verde", () => {
    render(<AppHeader />);

    expect(screen.getByTestId("app-header")).toHaveClass(
      "bg-vornia-azul-profundo",
    );
    expect(screen.getByTestId("app-header")).toHaveClass(
      "border-vornia-verde-suave",
    );
  });
});
