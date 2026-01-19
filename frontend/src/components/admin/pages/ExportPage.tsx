import * as React from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { API_BASE } from '@/services/api';
import { logError } from '@/services/logger';
import { useAdminStore } from '@/stores';

type ExportFormat = 'csv' | 'json' | 'xlsx';
type ExportScope = 'sessions' | 'conversations';

function toIsoParam(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const d = new Date(trimmed);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

function parseFilename(contentDisposition: string | null, fallback: string) {
  if (!contentDisposition) return fallback;
  const match = /filename="([^"]+)"/.exec(contentDisposition);
  return match?.[1] || fallback;
}

export function ExportPage() {
  const { token } = useAdminStore();

  const [scope, setScope] = React.useState<ExportScope>('conversations');
  const [format, setFormat] = React.useState<ExportFormat>('csv');
  const [start, setStart] = React.useState('');
  const [end, setEnd] = React.useState('');
  const [userName, setUserName] = React.useState('');
  const [topic, setTopic] = React.useState('');
  const [keyword, setKeyword] = React.useState('');
  const [minDepth, setMinDepth] = React.useState('');
  const [maxDepth, setMaxDepth] = React.useState('');
  const [limit, setLimit] = React.useState(5000);

  const [downloading, setDownloading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const download = React.useCallback(async () => {
    if (!token) {
      setError('缺少 Token（右上角设置）');
      return;
    }

    setDownloading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set('scope', scope);
      params.set('format', format);
      params.set('limit', String(limit));

      const s = toIsoParam(start);
      const e = toIsoParam(end);
      if (s) params.set('start', s);
      if (e) params.set('end', e);
      if (userName.trim()) params.set('user_name', userName.trim());
      if (topic.trim()) params.set('topic', topic.trim());
      if (keyword.trim()) params.set('keyword', keyword.trim());
      if (minDepth.trim()) params.set('min_depth', minDepth.trim());
      if (maxDepth.trim()) params.set('max_depth', maxDepth.trim());

      const resp = await fetch(`${API_BASE}/admin/export?${params.toString()}`, {
        headers: { 'X-Admin-Token': token },
      });

      if (!resp.ok) {
        const maybeJson = await resp.text();
        throw new Error(maybeJson || `HTTP ${resp.status}`);
      }

      const blob = await resp.blob();
      const defaultName = `export.${format}`;
      const filename = parseFilename(resp.headers.get('content-disposition'), defaultName);

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      logError('ExportPage', '下载失败', e);
      const msg = e instanceof Error ? e.message : '下载失败';
      setError(msg);
    } finally {
      setDownloading(false);
    }
  }, [token, scope, format, limit, start, end, userName, topic, keyword, minDepth, maxDepth]);

  return (
    <div className="space-y-4">
      <Card className="card-interactive">
        <CardHeader>
          <CardTitle className="text-base">会话记录导出</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">导出范围</div>
              <div className="flex gap-2">
                <Button variant={scope === 'conversations' ? 'default' : 'outline'} onClick={() => setScope('conversations')}>
                  对话记录
                </Button>
                <Button variant={scope === 'sessions' ? 'default' : 'outline'} onClick={() => setScope('sessions')}>
                  会话表
                </Button>
              </div>
            </div>

            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">格式</div>
              <div className="flex gap-2">
                {(['csv', 'json', 'xlsx'] as ExportFormat[]).map((f) => (
                  <Button key={f} variant={format === f ? 'default' : 'outline'} onClick={() => setFormat(f)}>
                    {f.toUpperCase()}
                  </Button>
                ))}
              </div>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">开始时间</div>
              <Input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">结束时间</div>
              <Input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Limit</div>
              <Input type="number" min={1} max={20000} value={limit} onChange={(e) => setLimit(Number(e.target.value || 5000))} />
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">user_name</div>
              <Input value={userName} onChange={(e) => setUserName(e.target.value)} placeholder="精确匹配" />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">topic</div>
              <Input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="精确匹配" />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">keyword</div>
              <Input value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="匹配 question/answer" />
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">min_depth</div>
              <Input value={minDepth} onChange={(e) => setMinDepth(e.target.value)} placeholder=">= 0" />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">max_depth</div>
              <Input value={maxDepth} onChange={(e) => setMaxDepth(e.target.value)} placeholder="<= 4" />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={download} disabled={downloading}>
              {downloading ? '下载中...' : '下载'}
            </Button>
            <span className="text-xs text-muted-foreground">
              请求头: <code>X-Admin-Token</code>
            </span>
          </div>

          {error ? <p className="text-sm text-destructive">{error}</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}

