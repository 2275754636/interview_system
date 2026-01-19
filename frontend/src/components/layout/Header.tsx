import { Button } from "@/components/ui/button";
import { lazyLoad } from "@/lib/lazy";
import { Command, Share2 } from "lucide-react";
import { useRef, useState } from "react";
import type { ReactNode } from "react";

const LazyQRCodeDialog = lazyLoad(
  () =>
    import("@/components/QRCodeDialog").then((m) => ({
      default: m.QRCodeDialog,
    }))
);

interface HeaderProps {
  title: string;
  subtitle?: string;
  onCommandOpen?: () => void;
  actions?: ReactNode;
}

export function Header({ title, subtitle, onCommandOpen, actions }: HeaderProps) {
  const [shareOpen, setShareOpen] = useState(false);
  const didWarmupShare = useRef(false);
  const didWarmupCommand = useRef(false);

  const warmupShare = () => {
    if (didWarmupShare.current) return;
    didWarmupShare.current = true;
    void import("@/components/QRCodeDialog");
    void import("qrcode.react");
  };

  const warmupCommand = () => {
    if (didWarmupCommand.current) return;
    didWarmupCommand.current = true;
    void import("@/components/common/CommandPalette");
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex flex-col">
          <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
          {subtitle && (
            <p className="text-sm text-muted-foreground">{subtitle}</p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {actions ? actions : null}

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShareOpen(true)}
            onPointerEnter={warmupShare}
            onFocus={warmupShare}
            className="gap-2"
          >
            <Share2 className="h-4 w-4" />
            <span className="hidden sm:inline">分享</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onCommandOpen}
            onPointerEnter={warmupCommand}
            onFocus={warmupCommand}
            className="gap-2"
          >
            <Command className="h-4 w-4" />
            <span className="hidden sm:inline">Ctrl+K</span>
          </Button>
        </div>
      </div>

      {shareOpen ? (
        <LazyQRCodeDialog open={shareOpen} onOpenChange={setShareOpen} />
      ) : null}
    </header>
  );
}
