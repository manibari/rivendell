"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronLeft } from "lucide-react";
import { apiFetch, type DocContent } from "@/lib/api";

// /docs/<path> renders one markdown file from rivendell/docs/ — the deep-dive
// pages the role view links to (docs/loops/gov-tender.md and friends).
export default function DocPage() {
  const params = useParams<{ slug: string[] }>();
  const slug = Array.isArray(params.slug) ? params.slug.join("/") : String(params.slug ?? "");
  const [doc, setDoc] = useState<DocContent | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    apiFetch<DocContent>(`/api/docs/${slug}`).then(setDoc).catch((e) => setErr(e.message));
  }, [slug]);

  if (err) return <p style={{ color: "var(--status-err)" }}>Error: {err}</p>;
  if (!doc) return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  return (
    <div style={{ maxWidth: 1080 }}>
      <div className="mb-3 flex items-center gap-3">
        <Link href="/skills/roles" className="inline-flex items-center gap-1 text-xs" style={{ color: "var(--text-muted)" }}>
          <ChevronLeft size={14} /> 角色 → 工作 → PDCA
        </Link>
        <span className="font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
          {doc.path}
        </span>
      </div>
      <article
        className="prose prose-sm max-w-none p-6"
        style={{ color: "var(--text)", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}
      >
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{doc.content}</ReactMarkdown>
      </article>
    </div>
  );
}
