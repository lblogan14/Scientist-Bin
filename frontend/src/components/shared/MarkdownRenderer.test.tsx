import { render, screen } from "@testing-library/react";
import { MarkdownRenderer } from "./MarkdownRenderer";

describe("MarkdownRenderer", () => {
  it("renders markdown headings", () => {
    render(<MarkdownRenderer content="# Hello World" />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Hello World",
    );
  });

  it("renders paragraphs", () => {
    render(<MarkdownRenderer content="Some text here." />);
    expect(screen.getByText("Some text here.")).toBeInTheDocument();
  });

  it("renders bold text", () => {
    render(<MarkdownRenderer content="**bold text**" />);
    expect(screen.getByText("bold text")).toBeInTheDocument();
    expect(screen.getByText("bold text").tagName).toBe("STRONG");
  });

  it("renders a GFM table", () => {
    const markdown = `| A | B |\n|---|---|\n| 1 | 2 |`;
    render(<MarkdownRenderer content={markdown} />);
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("renders unordered lists", () => {
    render(<MarkdownRenderer content={"- item 1\n- item 2"} />);
    expect(screen.getAllByRole("listitem").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/item 1/)).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(
      <MarkdownRenderer content="test" className="my-class" />,
    );
    expect(container.firstChild).toHaveClass("my-class");
  });

  it("renders empty string without crashing", () => {
    const { container } = render(<MarkdownRenderer content="" />);
    expect(container.firstChild).toBeInTheDocument();
  });
});
