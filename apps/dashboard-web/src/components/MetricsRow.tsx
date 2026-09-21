interface Metric {
  label: string;
  value: string | number;
}

export default function MetricsRow({ metrics }: { metrics: Metric[] }) {
  return (
    <div
      className={`grid grid-cols-2 gap-4 ${
        metrics.length <= 4 ? "sm:grid-cols-4" : "sm:grid-cols-3 lg:grid-cols-5"
      }`}
    >
      {metrics.map((m) => (
        <div
          key={m.label}
          className="p-4"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
          }}
        >
          <p
            className="font-mono text-[10px] uppercase"
            style={{
              color: "var(--text-subtle)",
              letterSpacing: "0.1em",
            }}
          >
            {m.label}
          </p>
          <p
            className="mt-1 tabular-nums"
            style={{
              color: "var(--text)",
              fontSize: 24,
              fontWeight: 500,
              fontFamily: "var(--font-mono)",
            }}
          >
            {m.value}
          </p>
        </div>
      ))}
    </div>
  );
}
