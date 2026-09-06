"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronLeft } from "lucide-react";
import { apiFetch, type SkillInfo, type SkillRolesDoc } from "@/lib/api";

// Renders docs/skills-by-role.md verbatim. The markdown is the source of
// truth (sk check guards that every skill appears in it); this page only
// turns `name` code spans that match a deployed skill into /skills/<name>
// links. Everything else (paths, commands) stays plain code.
export default function SkillRolesPage() {
  const [doc, setDoc] = useState<SkillRolesDoc | null>(null);
  const [names, setNames] = useState<Set<string>>(() => new Set());
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<SkillRolesDoc>("/api/skills/roles")
      .then(setDoc)
      .catch((e) => setErr(e.message));
    apiFetch<SkillInfo[]>("/api/skills")
      .then((list) => setNames(new Set(list.map((s) => s.name))))
      .catch(() => {});
  }, []);

  const components = useMemo(
    () => ({
      code: ({ children, className }: { children?: React.ReactNode; className?: string }) => {
        const text = String(children).trim();
        if (!className && names.has(text)) {
          return (
            <Link
              href={`/skills/${encodeURIComponent(text)}`}
              className="font-mono no-underline"
              style={{
                color: "var(--accent)",
                background: "var(--accent-bg)",
                borderRadius: 2,
                padding: "0 4px",
                fontSize: "0.9em",
                fontWeight: 500,
              }}
            >
              {text}
            </Link>
          );
        }
        return (
          <code className={`font-mono ${className ?? ""}`} style={{ fontSize: "0.9em" }}>
            {children}
          </code>
        );
      },
    }),
    [names],
  );

  if (err) return <p style={{ color: "var(--status-err)" }}>Error: {err}</p>;
  if (!doc) return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  return (
    <div style={{ maxWidth: 1080 }}>
      <Link
        href="/skills"
        className="mb-4 inline-flex items-center gap-1 text-xs"
        style={{ color: "var(--text-muted)" }}
      >
        <ChevronLeft size={14} /> Skill 總覽
      </Link>
      <p className="mb-4 font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
        source: {doc.path.replace(/^.*\/rivendell\//, "")} · 綠色 = 可點進 skill
      </p>
      <article
        className="prose prose-sm max-w-none p-6"
        style={{
          color: "var(--text)",
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
        }}
      >
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
          {doc.content}
        </ReactMarkdown>
      </article>
    </div>
  );
}
