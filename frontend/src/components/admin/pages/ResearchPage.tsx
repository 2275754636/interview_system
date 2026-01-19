import * as React from 'react';
import { useQuery } from '@tanstack/react-query';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { adminApi } from '@/services/api';
import { useAdminStore } from '@/stores';
import type { AdminListResponse, AdminSearchRow } from '@/types';

function toIsoParam(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const d = new Date(trimmed);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

function buildParams(input: Record<string, string>): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(input)) {
    const trimmed = v.trim();
    if (!trimmed) continue;
    out[k] = trimmed;
  }
  return out;
}

export function ResearchPage() {
  const { token } = useAdminStore();
  const [keyword, setKeyword] = React.useState('');
  const [topic, setTopic] = React.useState('');
  const [userName, setUserName] = React.useState('');
  const [start, setStart] = React.useState('');
  const [end, setEnd] = React.useState('');
  const [minDepth, setMinDepth] = React.useState('');
  const [maxDepth, setMaxDepth] = React.useState('');
  const [limit, setLimit] = React.useState(50);
  const [offset, setOffset] = React.useState(0);

  const params = React.useMemo(() => {
    const s = toIsoParam(start);
    const e = toIsoParam(end);
    return buildParams({
      keyword,
      topic,
      user_name: userName,
      start: s || '',
      end: e || '',
      min_depth: minDepth,
      max_depth: maxDepth,
      limit: String(limit),
      offset: String(offset),
    });
  }, [keyword, topic, userName, start, end, minDepth, maxDepth, limit, offset]);

  const query = useQuery<AdminListResponse<AdminSearchRow>>({
    queryKey: ['admin', 'search', params, token],
    queryFn: () => adminApi.search(params, token),
    enabled: !!token,
  });

  const total = query.data?.total || 0;
  const items = query.data?.items || [];
  const canPrev = offset > 0;
  const canNext = offset + limit < total;

  return (
    <div className="space-y-4">
      <Card className="card-interactive">
        <CardHeader>
          <CardTitle className="text-base">研究工具</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!token ? (
            <p className="text-sm text-muted-foreground">请先设置后台监管 Token（右上角）。</p>
          ) : null}

          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">keyword</div>
              <Input value={keyword} onChange={(e) => { setKeyword(e.target.value); setOffset(0); }} placeholder="匹配 question/answer" />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">topic</div>
              <Input value={topic} onChange={(e) => { setTopic(e.target.value); setOffset(0); }} placeholder="精确匹配" />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">user_name</div>
              <Input value={userName} onChange={(e) => { setUserName(e.target.value); setOffset(0); }} placeholder="精确匹配" />
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">开始时间</div>
              <Input type="datetime-local" value={start} onChange={(e) => { setStart(e.target.value); setOffset(0); }} />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">结束时间</div>
              <Input type="datetime-local" value={end} onChange={(e) => { setEnd(e.target.value); setOffset(0); }} />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">分页</div>
              <div className="flex gap-2">
                <Input type="number" min={1} max={500} value={limit} onChange={(e) => { setLimit(Number(e.target.value || 50)); setOffset(0); }} className="w-28" />
                <Button variant="outline" onClick={() => query.refetch()} disabled={query.isFetching || !token}>
                  {query.isFetching ? '查询中...' : '查询'}
                </Button>
              </div>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">min_depth</div>
              <Input value={minDepth} onChange={(e) => { setMinDepth(e.target.value); setOffset(0); }} placeholder=">= 0" />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">max_depth</div>
              <Input value={maxDepth} onChange={(e) => { setMaxDepth(e.target.value); setOffset(0); }} placeholder="<= 4" />
            </div>
          </div>

          {query.isError ? (
            <p className="text-sm text-destructive">
              {(query.error as Error)?.message || '查询失败'}
            </p>
          ) : null}

          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="text-sm text-muted-foreground">
              总计: <span className="tabular-nums">{total}</span>，当前: <span className="tabular-nums">{items.length}</span>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={() => setOffset(Math.max(0, offset - limit))} disabled={!canPrev}>
                上一页
              </Button>
              <Button variant="outline" onClick={() => setOffset(offset + limit)} disabled={!canNext}>
                下一页
              </Button>
            </div>
          </div>

          <ScrollArea className="h-[420px] rounded-md border">
            <div className="min-w-[900px] p-2">
              <div className="grid grid-cols-[160px_140px_120px_80px_1fr] gap-2 border-b p-2 text-xs font-semibold text-muted-foreground">
                <div>timestamp</div>
                <div>user</div>
                <div>topic</div>
                <div>depth</div>
                <div>question / answer</div>
              </div>
              {items.map((r) => (
                <div key={r.id} className="grid grid-cols-[160px_140px_120px_80px_1fr] gap-2 border-b p-2 text-xs">
                  <div className="font-mono text-muted-foreground">{r.timestamp}</div>
                  <div className="truncate">{r.userName || '(空)'}</div>
                  <div className="truncate">{r.topic || '(空)'}</div>
                  <div className="tabular-nums">{r.depthScore}</div>
                  <div className="space-y-1">
                    <div className="truncate">
                      <span className="text-muted-foreground">Q: </span>
                      {r.question}
                    </div>
                    <div className="truncate">
                      <span className="text-muted-foreground">A: </span>
                      {r.answer}
                    </div>
                    <div className="font-mono text-[10px] text-muted-foreground">
                      session: {r.sessionId}
                    </div>
                  </div>
                </div>
              ))}
              {!items.length && !query.isFetching ? (
                <div className="p-6 text-center text-sm text-muted-foreground">暂无结果</div>
              ) : null}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
