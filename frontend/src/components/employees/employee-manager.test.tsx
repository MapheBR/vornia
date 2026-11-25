import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EmployeeManager } from "@/components/employees/employee-manager";

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

const employee = {
  id: "e1",
  name: "Maria Silva",
  registration: "M-1",
  cpf: "526.018.159-06",
  pis: null,
  job_title: "Analista",
  department: "RH",
  is_active: true,
  hired_at: null,
  created_at: "2026-11-25T10:00:00Z",
  updated_at: "2026-11-25T10:00:00Z",
};

function listPayload(data = [employee]) {
  return {
    data,
    meta: { total: data.length, page: 1, per_page: 20, total_pages: 1 },
  };
}

describe("EmployeeManager", () => {
  beforeEach(() => {
    apiFetchMock.mockReset();
    apiFetchMock.mockResolvedValue(listPayload());
  });

  it("carrega e exibe a lista de colaboradores", async () => {
    render(<EmployeeManager />);
    expect(await screen.findByText("Maria Silva")).toBeInTheDocument();
    expect(apiFetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/employees"),
    );
  });

  it("abre o formulário e cria um colaborador", async () => {
    const user = userEvent.setup();
    render(<EmployeeManager />);
    await screen.findByText("Maria Silva");

    await user.click(screen.getByRole("button", { name: /novo colaborador/i }));
    await user.type(screen.getByLabelText(/^nome$/i), "João Santos");
    await user.type(screen.getByLabelText(/cpf/i), "890.786.666-09");
    await user.click(screen.getByRole("button", { name: /salvar/i }));

    await waitFor(() => {
      expect(apiFetchMock).toHaveBeenCalledWith(
        "/employees",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("busca colaboradores pelo termo digitado", async () => {
    const user = userEvent.setup();
    render(<EmployeeManager />);
    await screen.findByText("Maria Silva");

    await user.type(screen.getByPlaceholderText(/buscar/i), "Maria");
    await waitFor(() => {
      expect(apiFetchMock).toHaveBeenCalledWith(
        expect.stringContaining("search=Maria"),
      );
    });
  });
});
