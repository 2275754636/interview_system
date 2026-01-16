import { Button } from '@/components/ui/button';

interface ActionBarProps {
  onUndo?: () => void;
  onSkip?: () => void;
  onRestart?: () => void;
  canUndo?: boolean;
  canSkip?: boolean;
}

export function ActionBar({
  onUndo,
  onSkip,
  onRestart,
  canUndo = false,
  canSkip = false,
}: ActionBarProps) {
  return (
    <div className="flex gap-2">
      {onUndo && (
        <Button variant="outline" size="sm" onClick={onUndo} disabled={!canUndo}>
          撤回
        </Button>
      )}
      {onSkip && (
        <Button variant="outline" size="sm" onClick={onSkip} disabled={!canSkip}>
          跳过
        </Button>
      )}
      {onRestart && (
        <Button variant="ghost" size="sm" onClick={onRestart}>
          重新开始
        </Button>
      )}
    </div>
  );
}
