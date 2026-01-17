import { QueryClient } from '@tanstack/react-query';

export const DEFAULT_STALE_TIME_MS = 1000 * 60 * 5;
export const DEFAULT_GC_TIME_MS = 1000 * 60 * 10;

export const STATS_REFETCH_INTERVAL_MS = 1000 * 30;
export const STATS_STALE_TIME_MS = 1000 * 30;

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: DEFAULT_STALE_TIME_MS,
      gcTime: DEFAULT_GC_TIME_MS,
    },
  },
});
