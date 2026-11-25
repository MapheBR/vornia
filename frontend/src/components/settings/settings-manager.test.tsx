import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SettingsManager } from "@/components/settings/settings-manager";

const apiFetchMock = vi.fn();

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

describe("SettingsManager", () => {
  beforeEach(() => {
    apiFetchMock.mockReset();
    apiFetchMock.mockResolvedValue({
      data: {
        timezone: "America/Sao_Paulo",
        workday_minutes: 480,
        tolerance_minutes: 5,
        lunch_minutes: 60,
        overtime_enabled: false,
        week_start: 1,
      },
    });
  });

  it("carrega e exibe as chaves de configuração", async () => {
    render(<SettingsManager />);
    expect(await screen.findByText(/America\/Sao_Paulo/)).toBeInTheDocument();
    expect(apiFetchMock).toHaveBeenCalledWith("/settings");
  });

  it("salva uma chave com valor JSON", async () => {
    const user = userEvent.setup();
    render(<SettingsManager />);
    await screen.findByText(/America\/Sao_Paulo/);

    await user.type(screen.getByLabelText(/chave/i), "timezone");
    const valueInput = screen.getByLabelText(/valor/i);
    await user.clear(valueInput);
    await user.type(valueInput, '"Europe/London"');
    await user.click(screen.getByRole("button", { name: /salvar/i }));

    await waitFor(() => {
      expect(apiFetchMock).toHaveBeenCalledWith(
        "/settings/timezone",
        expect.objectContaining({
          method: "PUT",
          body: JSON.stringify({ value: "Europe/London" }),
        }),
      );
    });
  });

  it("rejeita valor JSON inválido antes de chamar a API", async () => {
    const user = userEvent.setup();
    render(<SettingsManager />);
    await screen.findByText(/America\/Sao_Paulo/);

    await user.type(screen.getByLabelText(/chave/i), "timezone");
    await user.type(screen.getByLabelText(/valor/i), "nao-e-json");
    await user.click(screen.getByRole("button", { name: /salvar/i }));

    expect(await screen.findByText(/json válido/i)).toBeInTheDocument();
    expect(apiFetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("/settings/timezone"),
      expect.anything(),
    );
  });
});
