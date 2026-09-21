type Status = "ok" | "warn" | "err" | "idle";

interface StatusDotProps {
  status: Status;
  label?: string;
  size?: number;
}

const STATUS_VAR: Record<Status, string> = {
  ok: "var(--status-ok)",
  warn: "var(--status-warn)",
  err: "var(--status-err)",
  idle: "var(--text-subtle)",
};

export default function StatusDot({
  status,
  label,
  size = 8,
}: StatusDotProps) {
  return (
    <span className="inline-flex items-center gap-2">
      <span
        aria-hidden
        style={{
          width: size,
          height: size,
          borderRadius: "50%",
          background: STATUS_VAR[status],
          flexShrink: 0,
          display: "inline-block",
        }}
      />
      {label && <span className="font-mono text-xs">{label}</span>}
    </span>
  );
}
