import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Header } from "@/components/layout/Header";

describe("Header", () => {
  it("renders title", () => {
    render(<Header title="Test Title" />);
    expect(screen.getByText("Test Title")).toBeInTheDocument();
  });

  it("renders subtitle when provided", () => {
    render(<Header title="Title" subtitle="Test Subtitle" />);
    expect(screen.getByText("Test Subtitle")).toBeInTheDocument();
  });

  it("does not render subtitle when not provided", () => {
    render(<Header title="Title" />);
    expect(screen.queryByText("Test Subtitle")).not.toBeInTheDocument();
  });

  it("calls onCommandOpen when button clicked", async () => {
    const user = userEvent.setup();
    const handleCommandOpen = vi.fn();

    render(<Header title="Title" onCommandOpen={handleCommandOpen} />);

    const button = screen.getByRole("button", { name: /ctrl\+k/i });
    await user.click(button);

    expect(handleCommandOpen).toHaveBeenCalledTimes(1);
  });

  it("renders share button", () => {
    render(<Header title="Title" />);
    expect(screen.getByRole("button", { name: /分享/i })).toBeInTheDocument();
  });
});
