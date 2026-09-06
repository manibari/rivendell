"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronLeft } from "lucide-react";
import { apiFetch, type SkillRolesData } from "@/lib/api";
import RolePdca from "@/components/RolePdca";

// /skills/roles — the structured 角色 → 工作 → PDCA view. `?raw=1` shows the
// markdown source instead (the same file, rendered as prose).
function RawDoc() {
  const [doc, setDoc] = useState<SkillRolesData | null>(null);
  useEffect(() => {
    apiFetch<SkillRolesData>("/api/skills/roles").then(setDoc).catch(() => {});
  }, []);
  if (!doc) return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;
  return (
    <article
      className="prose prose-sm max-w-none p-6"
      style={{ color: "var(--text)", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{doc.content}</ReactMarkdown>
    </article>
  );
}

function RolesInner() {
  const params = useSearchParams();
  const raw = params.get("raw") === "1";
  const role = params.get("role") ?? undefined;
  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <Link href="/skills" className="inline-flex items-center gap-1 text-xs" style={{ color: "var(--text-muted)" }}>
          <ChevronLeft size={14} /> Skill 總覽
        </Link>
        <h1 className="tracking-tight" style={{ fontSize: 22, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.02em" }}>
          角色 → 工作 → PDCA
        </h1>
        {raw && (
          <Link href="/skills/roles" className="text-xs" style={{ color: "var(--accent)" }}>
            結構化視圖 →
          </Link>
        )}
      </div>
      {raw ? <RawDoc /> : <RolePdca initialRole={role} />}
    </div>
  );
}

export default function SkillRolesPage() {
  return (
    <Suspense fallback={<p style={{ color: "var(--text-muted)" }}>載入中...</p>}>
      <RolesInner />
    </Suspense>
  );
}
