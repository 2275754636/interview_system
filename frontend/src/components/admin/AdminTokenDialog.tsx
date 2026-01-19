import * as React from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { adminApi } from '@/services/api';
import { logError } from '@/services/logger';
import { useAdminStore } from '@/stores';

export interface AdminTokenDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AdminTokenDialog({ open, onOpenChange }: AdminTokenDialogProps) {
  const { token, setToken, clearToken } = useAdminStore();
  const [value, setValue] = React.useState(token);
  const [checking, setChecking] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [ok, setOk] = React.useState(false);

  React.useEffect(() => {
    if (!open) return;
    setValue(token);
    setError(null);
    setOk(false);
  }, [open, token]);

  const handleVerify = React.useCallback(async () => {
    const trimmed = value.trim();
    if (!trimmed) {
      setError('请输入 Token');
      return;
    }
    setChecking(true);
    setError(null);
    try {
      await adminApi.overview({ bucket: 'day', top_n: '1' }, trimmed);
      setOk(true);
      setToken(trimmed);
    } catch (e) {
      logError('AdminTokenDialog', '验证失败', e);
      const msg = e instanceof Error ? e.message : '验证失败';
      setOk(false);
      setError(msg);
    } finally {
      setChecking(false);
    }
  }, [setToken, value]);

  const handleClear = React.useCallback(() => {
    clearToken();
    setValue('');
    setOk(false);
    setError(null);
  }, [clearToken]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>后台监管 Token</DialogTitle>
          <DialogDescription>
            需要后端设置 <code>ADMIN_TOKEN</code>，请求会携带 <code>X-Admin-Token</code>。
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <Input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="输入 Token"
            autoComplete="off"
          />

          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={handleVerify} disabled={checking}>
              {checking ? '验证中...' : '验证并保存'}
            </Button>
            <Button variant="outline" onClick={handleClear} disabled={checking}>
              清除
            </Button>
            {ok ? <span className="text-sm text-emerald-600">已验证</span> : null}
          </div>

          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          <p className="text-xs text-muted-foreground">
            Token 存储在浏览器本地（localStorage）。
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

