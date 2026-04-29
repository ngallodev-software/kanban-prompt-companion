import { cn } from "@/lib/cn";

type MarkdownBlock =
  | { kind: "heading"; level: 1 | 2 | 3; text: string }
  | { kind: "list"; items: string[] }
  | { kind: "paragraph"; lines: string[] }
  | { kind: "code"; lines: string[] };

function parseMarkdown(input: string): MarkdownBlock[] {
  const lines = input.replace(/\r\n/g, "\n").split("\n");
  const blocks: MarkdownBlock[] = [];
  let paragraph: string[] = [];
  let listItems: string[] = [];
  let codeLines: string[] = [];
  let inCode = false;

  const flushParagraph = () => {
    if (paragraph.length > 0) {
      blocks.push({ kind: "paragraph", lines: paragraph });
      paragraph = [];
    }
  };

  const flushList = () => {
    if (listItems.length > 0) {
      blocks.push({ kind: "list", items: listItems });
      listItems = [];
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();

    if (line.startsWith("```")) {
      if (inCode) {
        blocks.push({ kind: "code", lines: codeLines });
        codeLines = [];
      } else {
        flushParagraph();
        flushList();
      }
      inCode = !inCode;
      continue;
    }

    if (inCode) {
      codeLines.push(line);
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }

    const headingMatch = /^(#{1,3})\s+(.*)$/.exec(line);
    if (headingMatch) {
      flushParagraph();
      flushList();
      const headingLevel = headingMatch[1]?.length ?? 1;
      blocks.push({
        kind: "heading",
        level: headingLevel as 1 | 2 | 3,
        text: headingMatch[2] ?? "",
      });
      continue;
    }

    const listMatch = /^[-*]\s+(.*)$/.exec(line);
    if (listMatch) {
      flushParagraph();
      listItems.push(listMatch[1] ?? "");
      continue;
    }

    flushList();
    paragraph.push(line);
  }

  flushParagraph();
  flushList();
  if (inCode && codeLines.length > 0) {
    blocks.push({ kind: "code", lines: codeLines });
  }

  return blocks;
}

export function SafeMarkdownPreview({ markdown, className }: { markdown: string; className?: string }) {
  const blocks = parseMarkdown(markdown);

  return (
    <div className={cn("space-y-3 text-sm leading-6 text-text-primary", className)}>
      {blocks.length === 0 ? (
        <p className="text-text-tertiary">Nothing to preview.</p>
      ) : null}
      {blocks.map((block, index) => {
        if (block.kind === "heading") {
          const headingClass =
            block.level === 1
              ? "text-base font-semibold"
              : block.level === 2
                ? "text-sm font-semibold"
                : "text-sm font-medium text-text-secondary";
          return (
            <div key={`${block.kind}-${index}`} className={headingClass}>
              {block.text}
            </div>
          );
        }

        if (block.kind === "list") {
          return (
            <ul key={`${block.kind}-${index}`} className="space-y-1 pl-5">
              {block.items.map((item, itemIndex) => (
                <li key={`${block.kind}-${index}-${itemIndex}`} className="list-disc">
                  {item}
                </li>
              ))}
            </ul>
          );
        }

        if (block.kind === "code") {
          return (
            <pre
              key={`${block.kind}-${index}`}
              className="overflow-x-auto rounded-md border border-border bg-surface-2 px-3 py-2 text-xs leading-5 text-text-primary"
            >
              {block.lines.join("\n")}
            </pre>
          );
        }

        return (
          <p key={`${block.kind}-${index}`} className="whitespace-pre-wrap text-text-primary">
            {block.lines.join("\n")}
          </p>
        );
      })}
    </div>
  );
}
