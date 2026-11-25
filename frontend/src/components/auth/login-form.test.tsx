import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginForm } from "@/components/auth/login-form";

const apiFetchMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

vi.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetchMock(...args),
  ApiError: class ApiError extends Error {
    constructor(
      readonly status: number,
      readonly detail: string,
    ) {
      super(detail);
    }
  },
}));

describe("LoginForm", () => {
  beforeEach(() => {
    apiFetchMock.mockReset();
  });

  it("renderiza email e senha e envia POST /auth/login", async () => {
    apiFetchMock.mockResolvedValue({
      id: "1",
      email: "alice@acme.example.com",
      company_id: "c1",
      role: "admin",
    });
    const user = userEvent.setup();

    render(<LoginForm />);
    await user.type(screen.getByLabelText(/e-mail/i), "alice@acme.example.com");
    await user.type(screen.getByLabelText(/senha/i), "strong-password");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    await waitFor(() => {
      expect(apiFetchMock).toHaveBeenCalledWith(
        "/auth/login",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("mostra erro quando as credenciais são inválidas", async () => {
    apiFetchMock.mockRejectedValue(new Error("Invalid credentials"));
    const user = userEvent.setup();

    render(<LoginForm />);
    await user.type(screen.getByLabelText(/e-mail/i), "alice@acme.example.com");
    await user.type(screen.getByLabelText(/senha/i), "wrong");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByText(/credenciais inválidas/i)).toBeInTheDocument();
  });
});
