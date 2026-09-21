"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { type WorkflowId } from "../playbook-data";
import FlowView from "../FlowView";

const VALID_FLOWS = new Set<WorkflowId>(["ui", "backend", "slide", "maintenance"]);

export default function ProjectWorkflowFlowPage() {
  const params = useParams();
  const router = useRouter();
  const name = decodeURIComponent(params.name as string);
  const flow = params.flow as string;

  if (name !== "rivendell") {
    return (
      <div className="p-10" style={{ maxWidth: 720 }}>
        <Link
          href={`/projects/${encodeURIComponent(name)}`}
          className="inline-flex items-center gap-1.5 mb-6"
          style={{ color: "var(--text-muted)", fontSize: 13 }}
        >
          <ArrowLeft size={13} /> {name}
        </Link>
        <p style={{ color: "var(--text-muted)", fontSize: 14 }}>
          此專案沒有 workflow playbook。目前只有{" "}
          <code style={{ fontFamily: "var(--font-mono)" }}>rivendell</code>{" "}
          有對應的流程定義。
        </p>
      </div>
    );
  }

  if (!VALID_FLOWS.has(flow as WorkflowId)) {
    return (
      <div className="p-10" style={{ maxWidth: 720 }}>
        <Link
          href={`/projects/${encodeURIComponent(name)}/workflow/ui`}
          className="inline-flex items-center gap-1.5 mb-6"
          style={{ color: "var(--text-muted)", fontSize: 13 }}
        >
          <ArrowLeft size={13} /> Workflow Map
        </Link>
        <p style={{ color: "var(--text-muted)", fontSize: 14 }}>
          Unknown flow: <code style={{ fontFamily: "var(--font-mono)" }}>{flow}</code>
        </p>
      </div>
    );
  }

  const flowId = flow as WorkflowId;

  return (
    <div className="px-10 py-8" style={{ background: "var(--bg)", minHeight: "100vh" }}>
      <div className="mx-auto" style={{ maxWidth: 880 }}>
        {/* Breadcrumb back to project */}
        <button
          onClick={() => router.push(`/projects/${encodeURIComponent(name)}`)}
          className="inline-flex items-center gap-1.5 mb-6 transition-colors"
          style={{ color: "var(--text-muted)", fontSize: 13 }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.color = "var(--text)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.color = "var(--text-muted)")
          }
        >
          <ArrowLeft size={13} /> {name}
        </button>

        <h1
          style={{
            fontSize: 28,
            fontWeight: 500,
            letterSpacing: "-0.02em",
            color: "var(--text)",
          }}
        >
          Workflow Map
        </h1>
        <div
          className="mt-1.5"
          style={{
            color: "var(--text-subtle)",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
          }}
        >
          ~/.claude/CLAUDE.md · click any chip for trigger / skip
        </div>

        {/* Flow switching now lives in the sidebar (workflow.NAV nested
            children), so the page no longer renders its own tab strip. */}
        <section className="mt-8">
          <FlowView flowId={flowId} />
        </section>

        <div
          className="mt-16 text-center"
          style={{ color: "var(--text-subtle)", fontSize: 14 }}
        >
          ❦
        </div>
      </div>
    </div>
  );
}
