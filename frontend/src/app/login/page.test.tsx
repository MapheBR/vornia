import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import LoginPage from "@/app/login/page";

vi.mock("@/components/auth/login-form", () => ({
  LoginForm: () => <div data-testid="login-form" />,
}));

describe("LoginPage", () => {
  it("apresenta a marca e o formulario de acesso", () => {
    render(<LoginPage />);

    expect(screen.getByRole("img", { name: /vornia/i })).toBeInTheDocument();
    expect(screen.getByText(/entrar no vornia/i)).toBeInTheDocument();
    expect(screen.getByTestId("login-form")).toBeInTheDocument();
  });

  it("usa o verde Vornia no cartao de login", () => {
    render(<LoginPage />);

    expect(screen.getByTestId("login-card")).toHaveClass(
      "border-vornia-verde-suave",
    );
  });
});
