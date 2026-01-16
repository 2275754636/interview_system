import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Layout } from "@/components/layout/Layout";

describe("Layout", () => {
  it("renders children", () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });

  it("renders sidebar when provided", () => {
    render(
      <Layout sidebar={<div>Sidebar Content</div>}>
        <div>Main Content</div>
      </Layout>
    );

    expect(screen.getByText("Sidebar Content")).toBeInTheDocument();
    expect(screen.getByText("Main Content")).toBeInTheDocument();
  });

  it("applies correct layout classes", () => {
    const { container } = render(
      <Layout>
        <div>Content</div>
      </Layout>
    );

    const mainElement = container.querySelector("main");
    expect(mainElement).toHaveClass("flex-1", "p-4");
  });

  it("renders without sidebar", () => {
    const { container } = render(
      <Layout>
        <div>Content</div>
      </Layout>
    );

    const aside = container.querySelector("aside");
    expect(aside).not.toBeInTheDocument();
  });
});
