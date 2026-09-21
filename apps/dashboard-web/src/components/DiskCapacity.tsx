"use client";

import { useEffect, useState } from "react";
import { apiFetch, type HealthData, type DiskInfo } from "@/lib/api";
import StatusDot from "@/components/StatusDot";

// Map disk status → StatusDot status + a human label.
const STATUS_META: Record<
  DiskInfo["status"],
  { dot: "ok" | "warn" | "err"; label: string }
> = {
  ok: { dot: "ok", label: "正常" },
  warn: { dot: "warn", label: "偏高" },
  crit: { dot: "err", label: "危險" },
  error: { dot: "err", label: "檢查失敗" },
};

// Bar fill color: forest-green (brand data color) when healthy; status colors
// only when there is an actual problem to communicate. See DESIGN.md "Color".
function fillColor(status: DiskInfo["status"]): string {
  if (status === "crit" || status === "error") return "var(--status-err)";
  if (status === "warn") return "var(--status-warn)";
  return "var(--accent)";
}

export default function DiskCapacity() {
  const [disk, setDisk] = useState<DiskInfo | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<HealthData>("/api/health")
      .then((d) => setDisk(d.disk))
      .catch((e) => setErr(e.message));
  }, []);

  const meta = disk ? STATUS_META[disk.status] : null;
  const pct = disk ? Math.max(0, Math.min(100, disk.percent)) : 0;

  return (
    <div
      className="p-4"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-md)",
      }}
    >
      <div className="flex items-center justify-between">
        <p
          className="font-mono text-[10px] uppercase"
          style={{ color: "var(--text-subtle)", letterSpacing: "0.1em" }}
        >
          磁碟容量
        </p>
        {meta && <StatusDot status={meta.dot} label={meta.label} />}
      </div>

      {err && (
        <p className="mt-2 text-sm" style={{ color: "var(--status-err)" }}>
          無法讀取：{err}
        </p>
      )}

      {!err && !disk && (
        <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
          載入中...
        </p>
      )}

      {disk && disk.status !== "error" && (
        <>
          <div className="mt-1 flex items-baseline gap-2">
            <span
              className="tabular-nums"
              style={{
                color: "var(--text)",
                fontSize: 24,
                fontWeight: 500,
                fontFamily: "var(--font-mono)",
              }}
            >
              {disk.percent}%
            </span>
            <span
              className="tabular-nums"
              style={{
                color: "var(--text-muted)",
                fontSize: 13,
                fontFamily: "var(--font-mono)",
              }}
            >
              已用 {disk.used_gb}G · 剩 {disk.avail_gb}G
            </span>
          </div>

          {/* On APFS the three df numbers do NOT add up: size is the shared
              container, used is this volume only, avail is container-free. The
              remainder is the other volumes (System, VM/swap, Preboot) plus
              snapshots — spell it out rather than printing "399 / 460G · 剩 22.3G"
              and letting the reader do arithmetic that cannot work. */}
          {(() => {
            const other = Math.round((disk.size_gb - disk.used_gb - disk.avail_gb) * 10) / 10;
            if (other < 1) return null;
            return (
              <p
                className="mt-1 tabular-nums"
                style={{ color: "var(--text-subtle)", fontSize: 11, fontFamily: "var(--font-mono)" }}
                title="APFS 容器由多個磁區共用：size 是容器總量、used 只算這個磁區、avail 是容器剩餘，三者不相加。"
              >
                容器 {disk.size_gb}G，另 {other}G 為同容器的系統磁區與快照
              </p>
            );
          })()}

          {/* Usage bar — track on surface-2, fill in status color */}
          <div
            className="mt-3 overflow-hidden"
            style={{
              height: 8,
              background: "var(--surface-2)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            <div
              style={{
                width: `${pct}%`,
                height: "100%",
                background: fillColor(disk.status),
                transition: "width 0.15s ease",
              }}
            />
          </div>

          <p
            className="mt-2 font-mono text-[10px] uppercase"
            style={{ color: "var(--text-subtle)", letterSpacing: "0.08em" }}
          >
            {disk.mount} · warn ≥{disk.warn_threshold}% · crit ≥
            {disk.crit_threshold}%
          </p>
        </>
      )}

      {disk && disk.status === "error" && (
        <p className="mt-2 text-sm" style={{ color: "var(--status-err)" }}>
          {disk.error || "磁碟檢查失敗"}
        </p>
      )}
    </div>
  );
}
