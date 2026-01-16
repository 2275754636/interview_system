import { cn } from '@/lib/utils';

interface MessageSkeletonProps {
  count?: number;
}

export function MessageSkeleton({ count = 1 }: MessageSkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={cn('flex w-full', i % 2 === 0 ? 'justify-start' : 'justify-end')}>
          <div
            className={cn(
              'max-w-[80%] animate-pulse rounded-2xl bg-muted px-4 py-3',
              i % 2 === 0 ? 'rounded-bl-md' : 'rounded-br-md'
            )}
          >
            <div className="h-4 w-48 rounded bg-muted-foreground/20" />
            <div className="mt-2 h-3 w-16 rounded bg-muted-foreground/10" />
          </div>
        </div>
      ))}
    </>
  );
}
