interface LogoProps {
  size?: number;
  variant?: "full" | "mark" | "mono";
  className?: string;
  withWordmark?: boolean;
}

export default function Logo({
  size = 28,
  variant = "full",
  className = "",
  withWordmark,
}: LogoProps) {
  const showWordmark = withWordmark ?? variant === "full";
  const fillColor = variant === "mono" ? "currentColor" : "var(--accent)";

  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <svg
        viewBox="0 0 56 56"
        width={size}
        height={size}
        role="img"
        aria-label="rivendell logo"
        style={{ flexShrink: 0 }}
      >
        <path
          d="M 18 12 C 12 18, 10 28, 14 38 C 20 34, 26 28, 26 18 C 26 16, 24 13, 18 12 Z"
          fill={fillColor}
        />
        <path
          d="M 38 12 C 44 18, 46 28, 42 38 C 36 34, 30 28, 30 18 C 30 16, 32 13, 38 12 Z"
          fill={fillColor}
          fillOpacity={0.55}
        />
        <line
          x1="28" y1="14" x2="28" y2="46"
          stroke={fillColor}
          strokeWidth="1.2"
          strokeLinecap="round"
        />
      </svg>
      {showWordmark && (
        <span
          className="font-semibold tracking-tight"
          style={{
            color: variant === "mono" ? "currentColor" : "var(--accent)",
            fontSize: size * 0.65,
            letterSpacing: "-0.04em",
          }}
        >
          rivendell
        </span>
      )}
    </span>
  );
}
