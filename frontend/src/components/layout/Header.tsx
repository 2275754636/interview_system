import { Button } from "@/components/ui/button";
import { lazyLoad } from "@/lib/lazy";
import { Command, Share2 } from "lucide-react";
import { useState } from "react";

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
}

export function Header({ title, subtitle, onCommandOpen }: HeaderProps) {
  const [shareOpen, setShareOpen] = useState(false);

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
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShareOpen(true)}
            className="gap-2"
          >
            <Share2 className="h-4 w-4" />
            <span className="hidden sm:inline">分享</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onCommandOpen}
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
