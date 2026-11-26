import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BrandLogo } from "@/components/brand/logo";

describe("BrandLogo", () => {
  it("renderiza a logo com texto alternativo e caminho publico", () => {
    render(<BrandLogo width={180} />);

    const logo = screen.getByRole("img", { name: /vornia/i });
    expect(logo).toHaveAttribute("src", expect.stringContaining("logo"));
  });
});
