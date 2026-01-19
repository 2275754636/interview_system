import * as React from 'react';
import { useQuery } from '@tanstack/react-query';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { adminApi } from '@/services/api';
import { useAdminStore } from '@/stores';
import type { AdminOverviewResponse } from '@/types';
import { MiniLineChart } from '@/components/admin/charts/MiniLineChart';
import { MiniBarChart } from '@/components/admin/charts/MiniBarChart';

function toIsoParam(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const d = new Date(trimmed);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

function buildParams(input: { start: string; end: string; bucket: string; topN: number }) {
  const params: Record<string, string> = { bucket: input.bucket, top_n: String(input.topN) };
  const start = toIsoParam(input.start);
  const end = toIsoParam(input.end);
  if (start) params.start = start;
  if (end) params.end = end;
  return params;
}

export function OverviewPage() {
  const { token } = useAdminStore();
  const [bucket, setBucket] = React.useState<'day' | 'hour'>('day');
  const [topN, setTopN] = React.useState(10);
  const [start, setStart] = React.useState('');
  const [end, setEnd] = React.useState('');

  const params = React.useMemo(() => buildParams({ start, end, bucket, topN }), [start, end, bucket, topN]);

  const query = useQuery<AdminOverviewResponse>({
    queryKey: ['admin', 'overview', params, token],
    queryFn: () => adminApi.overview(params, token),
    enabled: !!token,
    staleTime: 15_000,
  });

  const data = query.data;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-2">
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">开始时间</div>
          <Input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} />
        </div>
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">结束时间</div>
          <Input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} />
        </div>
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">聚合</div>
          <div className="flex gap-2">
            <Button variant={bucket === 'day' ? 'default' : 'outline'} onClick={() => setBucket('day')}>
              天
            </Button>
            <Button
              variant={bucket === 'hour' ? 'default' : 'outline'}
              onClick={() => setBucket('hour')}
            >
              小时
            </Button>
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">TopN</div>
          <Input
            type="number"
            min={1}
            max={50}
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value || 10))}
            className="w-28"
          />
        </div>
        <Button variant="outline" onClick={() => query.refetch()} disabled={!token || query.isFetching}>
          {query.isFetching ? '刷新中...' : '刷新'}
        </Button>
      </div>

      {!token ? (
        <Card>
          <CardHeader>
            <CardTitle>需要 Token</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            请先设置后台监管 Token（右上角）。
          </CardContent>
        </Card>
      ) : null}

      {query.isError ? (
        <Card>
          <CardHeader>
            <CardTitle>加载失败</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-destructive">
            {(query.error as Error)?.message || '未知错误'}
          </CardContent>
        </Card>
      ) : null}

      {data ? (
        <>
          <div className="grid gap-3 md:grid-cols-4">
            <Card className="card-interactive">
              <CardHeader>
                <CardTitle className="text-sm text-muted-foreground">会话数</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold tabular-nums">
                {data.summary.totalSessions}
              </CardContent>
            </Card>
            <Card className="card-interactive">
              <CardHeader>
                <CardTitle className="text-sm text-muted-foreground">消息数</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold tabular-nums">
                {data.summary.totalMessages}
              </CardContent>
            </Card>
            <Card className="card-interactive">
              <CardHeader>
                <CardTitle className="text-sm text-muted-foreground">活跃用户</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold tabular-nums">
                {data.summary.activeUsers}
              </CardContent>
            </Card>
            <Card className="card-interactive">
              <CardHeader>
                <CardTitle className="text-sm text-muted-foreground">平均深度</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold tabular-nums">
                {data.summary.avgDepthScore.toFixed(2)}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <Card className="card-interactive">
              <CardHeader>
                <CardTitle className="text-sm">会话趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <MiniLineChart values={data.timeSeries.map((p) => p.sessions)} />
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <span>点数: {data.timeSeries.length}</span>
                  <span>起: {data.timeSeries[0]?.bucket || '-'}</span>
                  <span>止: {data.timeSeries[data.timeSeries.length - 1]?.bucket || '-'}</span>
                </div>
              </CardContent>
            </Card>

            <Card className="card-interactive">
              <CardHeader>
                <CardTitle className="text-sm">消息趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <MiniLineChart values={data.timeSeries.map((p) => p.messages)} stroke="hsl(var(--foreground))" />
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <Card className="card-interactive">
              <CardHeader>
                <CardTitle className="text-sm">用户活跃（Top）</CardTitle>
              </CardHeader>
              <CardContent>
                <MiniBarChart
                  data={data.topUsers.map((u) => ({ label: u.userName || '(空)', value: u.messages }))}
                />
              </CardContent>
            </Card>

            <Card className="card-interactive">
              <CardHeader>
                <CardTitle className="text-sm">主题分布（Top）</CardTitle>
              </CardHeader>
              <CardContent>
                <MiniBarChart
                  data={data.topTopics.map((t) => ({ label: t.topic || '(空)', value: t.messages }))}
                />
              </CardContent>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
}
