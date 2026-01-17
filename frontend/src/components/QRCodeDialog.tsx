import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { lazyLoad } from "@/lib/lazy";
import { publicUrlApi } from "@/services/api";
import type { PublicUrlResponse } from "@/types";

const LazyQRCodeSVG = lazyLoad(() =>
  import("qrcode.react").then((m) => ({ default: m.QRCodeSVG }))
);

export interface QRCodeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function QRCodeDialog({ open, onOpenChange }: QRCodeDialogProps) {
  const [loading, setLoading] = React.useState(false);
  const [data, setData] = React.useState<PublicUrlResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [copyError, setCopyError] = React.useState<string | null>(null);

  const fetchState = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await publicUrlApi.get();
      setData(result);
    } catch (e) {
      const message = e instanceof Error ? e.message : "未知错误";
      setError(message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (!open) return;
    setCopyError(null);
    void fetchState();
  }, [open, fetchState]);

  const isPublicEnabled = !!data?.isPublic && !!data?.url;

  const handleCopy = React.useCallback(async () => {
    const url = data?.url;
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      setCopyError(null);
    } catch (e) {
      console.error('[QRCodeDialog] 复制失败:', e);
      setCopyError("复制失败，请手动复制。");
    }
  }, [data?.url]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>分享</DialogTitle>
          <DialogDescription>公网可访问，请注意隐私。</DialogDescription>
        </DialogHeader>

        {loading && (
          <div className="space-y-3">
            <div className="h-48 w-48 rounded-md border bg-muted animate-pulse" />
            <div className="h-5 w-full rounded bg-muted animate-pulse" />
          </div>
        )}

        {!loading && error && (
          <div className="space-y-3">
            <p className="text-sm text-destructive">加载失败: {error}</p>
            <Button variant="outline" onClick={fetchState}>
              重试
            </Button>
          </div>
        )}

        {!loading && !error && !isPublicEnabled && (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              未启用公网模式。请使用 <code>python start.py --public</code> 启动后再尝试分享。
            </p>
          </div>
        )}

        {!loading && !error && isPublicEnabled && data?.url && (
          <div className="space-y-3">
            <LazyQRCodeSVG
              value={data.url}
              size={192}
              includeMargin
              fallback={
                <div className="h-48 w-48 rounded-md border bg-muted animate-pulse" />
              }
            />

            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 rounded-md border bg-muted/30 p-2 font-mono text-xs break-all">
                {data.url}
              </div>
              <Button variant="outline" size="sm" onClick={handleCopy}>
                复制
              </Button>
            </div>

            {copyError ? (
              <p className="text-xs text-destructive">{copyError}</p>
            ) : null}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
