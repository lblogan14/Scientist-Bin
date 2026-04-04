import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const components: Components = {
  h1: ({ children }) => (
    <h1 className="mt-6 mb-4 text-2xl font-bold text-foreground">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mt-5 mb-3 border-l-4 border-primary pl-3 text-xl font-bold text-primary/90">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="mt-4 mb-2 text-lg font-semibold text-primary/80">
      {children}
    </h3>
  ),
  h4: ({ children }) => (
    <h4 className="mt-3 mb-2 text-base font-semibold text-foreground">
      {children}
    </h4>
  ),
  p: ({ children }) => (
    <p className="mb-3 leading-relaxed text-foreground">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="mb-4 list-disc space-y-1.5 pl-6 text-foreground">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-4 list-decimal space-y-1.5 pl-6 text-foreground">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="leading-relaxed pl-1">{children}</li>,
  strong: ({ children }) => (
    <strong className="font-semibold text-primary/90">{children}</strong>
  ),
  em: ({ children }) => <em className="italic text-foreground">{children}</em>,
  code: ({ children, className }) => {
    const isBlock = className?.startsWith("language-");
    if (isBlock) {
      return (
        <code className="font-mono text-sm text-foreground">{children}</code>
      );
    }
    return (
      <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-sm text-foreground">
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="mb-4 overflow-x-auto rounded-lg border border-border bg-muted p-4 text-sm">
      {children}
    </pre>
  ),
  blockquote: ({ children }) => (
    <blockquote className="mb-4 rounded border-l-4 border-primary bg-primary/5 p-3 italic text-muted-foreground">
      {children}
    </blockquote>
  ),
  a: ({ children, href }) => (
    <a
      href={href}
      className="text-primary underline underline-offset-2 hover:opacity-80"
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  ),
  table: ({ children }) => (
    <div className="mb-4 overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-muted text-foreground">{children}</thead>
  ),
  tbody: ({ children }) => (
    <tbody className="divide-y divide-border">{children}</tbody>
  ),
  tr: ({ children }) => <tr className="hover:bg-muted/50">{children}</tr>,
  th: ({ children }) => (
    <th className="px-4 py-2 text-left font-semibold text-foreground">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-4 py-2 text-foreground">{children}</td>
  ),
  img: ({ src, alt }) => (
    <img
      src={src}
      alt={alt ?? ""}
      className="my-4 max-w-full rounded-lg border border-border"
      loading="lazy"
    />
  ),
  hr: () => <hr className="my-6 border-t border-primary/20" />,
};

export function MarkdownRenderer({
  content,
  className,
}: MarkdownRendererProps) {
  return (
    <div className={`max-w-none text-sm ${className ?? ""}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
