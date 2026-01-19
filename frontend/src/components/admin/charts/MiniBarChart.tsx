import * as React from 'react';

export interface BarDatum {
  label: string;
  value: number;
}

export interface MiniBarChartProps {
  data: BarDatum[];
}

export function MiniBarChart({ data }: MiniBarChartProps) {
  const max = Math.max(1, ...data.map((d) => d.value));

  if (!data.length) {
    return (
      <div className="flex h-[180px] w-full items-center justify-center text-sm text-muted-foreground">
        暂无数据
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {data.map((d) => {
        const pct = Math.round((d.value / max) * 100);
        return (
          <div key={d.label} className="space-y-1">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span className="truncate">{d.label}</span>
              <span className="tabular-nums">{d.value}</span>
            </div>
            <div className="h-2 w-full rounded bg-muted">
              <div
                className="h-2 rounded bg-primary transition-all"
                style={{ width: `${pct}%` }}
                aria-label={`${d.label}: ${d.value}`}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
