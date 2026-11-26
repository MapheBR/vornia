import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Dashboard } from "@/components/dashboard/dashboard";

const apiFetchMock = vi.fn();

vi.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetchMock(...args),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

describe("Dashboard", () => {
  it("mostra a identidade visual e os cartoes de resumo", async () => {
    apiFetchMock.mockResolvedValue({
      total_employees: 26,
      hours_worked: 100,
      inconsistencies: 2,
      pending_journeys: 3,
    });

    render(<Dashboard />);

    expect(screen.getByTestId("app-header")).toBeInTheDocument();
    expect(await screen.findByText("26")).toBeInTheDocument();
    const cardTitle = screen
      .getAllByText("Colaboradores")
      .find((element) => element.tagName === "P");
    expect(cardTitle?.parentElement).toHaveClass("border-vornia-verde-suave");
  });
});
