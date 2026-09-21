"use client";

import Link from "next/link";

type Variant = "default" | "optional" | "highlighted";

interface SkillChipProps {
  name: string;
  variant?: Variant;
  /** When true, render as a Next.js Link to /skills/[name]. Defaults to true. */
  asLink?: boolean;
  /** Extra click handler (e.g. selecting in cross-reference panel). */
  onClick?: (name: string) => void;
}

const variantStyles: Record<Variant, React.CSSProperties> = {
  default: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    color: "var(--text)",
  },
  optional: {
    background: "var(--surface)",
    border: "1px dashed var(--border)",
    color: "var(--text-muted)",
  },
  highlighted: {
    background: "var(--accent)",
    border: "1px solid var(--accent)",
    color: "var(--surface)",
  },
};

export default function SkillChip({
  name,
  variant = "default",
  asLink = true,
  onClick,
}: SkillChipProps) {
  const baseStyle: React.CSSProperties = {
    fontFamily: "var(--font-mono)",
    fontSize: 10,
    padding: "2px 6px",
    borderRadius: 2,
    display: "inline-block",
    maxWidth: "100%",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    cursor: onClick || asLink ? "pointer" : "default",
    transition: "border-color 0.15s ease",
    ...variantStyles[variant],
  };

  const display = name.startsWith("/") ? name : `/${name}`;

  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      e.preventDefault();
      e.stopPropagation();
      onClick(name);
    }
  };

  if (asLink && !onClick) {
    return (
      <Link
        href={`/skills/${encodeURIComponent(name.replace(/^\//, ""))}`}
        style={baseStyle}
      >
        {display}
      </Link>
    );
  }

  return (
    <span style={baseStyle} onClick={handleClick}>
      {display}
    </span>
  );
}
