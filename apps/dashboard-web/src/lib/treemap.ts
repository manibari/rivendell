import type { DiskTreeNode } from "@/lib/api";

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Tile {
  node: DiskTreeNode;
  x: number;
  y: number;
  w: number;
  h: number;
}

/**
 * Squarified treemap (Bruls, Huizing & van Wijk 2000).
 * Lays children of one level into `rect`, minimizing tile aspect ratios.
 * Children are expected pre-sorted by size desc (the snapshot does this).
 */
export function squarify(nodes: DiskTreeNode[], rect: Rect): Tile[] {
  const valued = nodes
    .filter((n) => n.size_kb > 0)
    .map((n) => ({ node: n, value: n.size_kb }));
  if (valued.length === 0) return [];

  const tiles: Tile[] = [];
  let { x, y, w, h } = rect;
  let remainingValue = valued.reduce((s, v) => s + v.value, 0);
  let i = 0;

  const worst = (row: { value: number }[], length: number, scale: number): number => {
    if (row.length === 0) return Infinity;
    let sum = 0;
    let max = 0;
    let min = Infinity;
    for (const r of row) {
      const a = r.value * scale;
      sum += a;
      if (a > max) max = a;
      if (a < min) min = a;
    }
    const l2 = length * length;
    const s2 = sum * sum;
    return Math.max((l2 * max) / s2, s2 / (l2 * min));
  };

  while (i < valued.length) {
    const scale = (w * h) / remainingValue; // value → px²
    const length = Math.min(w, h);
    const row: typeof valued = [];

    while (i < valued.length) {
      const candidate = [...row, valued[i]];
      if (row.length === 0 || worst(candidate, length, scale) <= worst(row, length, scale)) {
        row.push(valued[i]);
        i++;
      } else {
        break;
      }
    }

    const rowValue = row.reduce((s, r) => s + r.value, 0);
    const rowArea = rowValue * scale;

    if (w >= h) {
      const colW = rowArea / h;
      let oy = y;
      for (const r of row) {
        const tileH = (r.value * scale) / colW;
        tiles.push({ node: r.node, x, y: oy, w: colW, h: tileH });
        oy += tileH;
      }
      x += colW;
      w -= colW;
    } else {
      const rowH = rowArea / w;
      let ox = x;
      for (const r of row) {
        const tileW = (r.value * scale) / rowH;
        tiles.push({ node: r.node, x: ox, y, w: tileW, h: rowH });
        ox += tileW;
      }
      y += rowH;
      h -= rowH;
    }
    remainingValue -= rowValue;
  }

  return tiles;
}

/** KB → human "12.3 G" / "456 M" / "78 K". */
export function humanKB(kb: number): string {
  if (kb >= 1024 * 1024) return `${(kb / 1024 / 1024).toFixed(1)}G`;
  if (kb >= 1024) return `${(kb / 1024).toFixed(0)}M`;
  return `${kb}K`;
}

/**
 * Tile fill — sequential greens per DESIGN.md (light → forest), keyed to the
 * tile's share of its parent so bigger blocks read darker. Returns [fill, text].
 */
export function tileColors(value: number, maxValue: number): [string, string] {
  const t = maxValue > 0 ? Math.sqrt(value / maxValue) : 0; // 0..1
  // Interpolate #d1ddd5 (209,221,213) → #2d4a3e (45,74,62)
  const lerp = (a: number, b: number) => Math.round(a + (b - a) * t);
  const r = lerp(209, 45);
  const g = lerp(221, 74);
  const b = lerp(213, 62);
  const fill = `rgb(${r}, ${g}, ${b})`;
  // White text once the green is dark enough for contrast.
  const text = t > 0.45 ? "#ffffff" : "#0a0a0a";
  return [fill, text];
}
