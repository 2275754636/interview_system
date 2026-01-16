import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Sidebar } from "@/components/layout/Sidebar";

describe("Sidebar", () => {
  it("renders children in desktop view", () => {
    render(
      <Sidebar>
        <div>Sidebar Content</div>
      </Sidebar>
    );

    expect(screen.getByText("Sidebar Content")).toBeInTheDocument();
  });

  it("renders menu button for mobile", () => {
    render(
      <Sidebar>
        <div>Content</div>
      </Sidebar>
    );

    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("calls onToggle when sheet state changes", async () => {
    const user = userEvent.setup();
    const handleToggle = vi.fn();

    render(
      <Sidebar onToggle={handleToggle}>
        <div>Content</div>
      </Sidebar>
    );

    const button = screen.getByRole("button");
    await user.click(button);

    expect(handleToggle).toHaveBeenCalled();
  });

  it("applies correct responsive classes", () => {
    const { container } = render(
      <Sidebar>
        <div>Content</div>
      </Sidebar>
    );

    const aside = container.querySelector("aside");
    expect(aside).toHaveClass("hidden", "md:block");
  });

  it("controls sheet open state", () => {
    const { rerender } = render(
      <Sidebar isOpen={false}>
        <div>Content</div>
      </Sidebar>
    );

    rerender(
      <Sidebar isOpen={true}>
        <div>Content</div>
      </Sidebar>
    );

    expect(screen.getAllByText("Content")).toHaveLength(2);
  });
});
