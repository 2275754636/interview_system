import * as React from 'react';

type Point = { x: number; y: number };

function scalePoints(values: number[], width: number, height: number, padding: number): Point[] {
  const n = values.length;
  if (n === 0) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1e-9);
  const innerW = Math.max(width - padding * 2, 1);
  const innerH = Math.max(height - padding * 2, 1);

  return values.map((v, i) => {
    const x = padding + (n === 1 ? innerW / 2 : (i / (n - 1)) * innerW);
    const y = padding + (1 - (v - min) / range) * innerH;
    return { x, y };
  });
}

function toPolyline(points: Point[]): string {
  return points.map((p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(' ');
}

export interface MiniLineChartProps {
  values: number[];
  width?: number;
  height?: number;
  stroke?: string;
}

export function MiniLineChart({
  values,
  width = 520,
  height = 160,
  stroke = 'hsl(var(--primary))',
}: MiniLineChartProps) {
  const padding = 10;
  const points = React.useMemo(() => scalePoints(values, width, height, padding), [
    values,
    width,
    height,
    padding,
  ]);

  if (values.length === 0) {
    return (
      <div className="flex h-[160px] w-full items-center justify-center text-sm text-muted-foreground">
        暂无数据
      </div>
    );
  }

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="max-w-full">
      <rect x="0" y="0" width={width} height={height} rx="12" fill="transparent" />
      <polyline
        fill="none"
        stroke={stroke}
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
        points={toPolyline(points)}
      />
      {points.map((p, idx) => (
        <circle key={idx} cx={p.x} cy={p.y} r="2.5" fill={stroke} opacity="0.85" />
      ))}
    </svg>
  );
}

