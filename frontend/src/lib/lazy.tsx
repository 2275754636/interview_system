/* eslint-disable react-refresh/only-export-components */
/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  lazy,
  Suspense,
  type ComponentProps,
  type ComponentType,
  type LazyExoticComponent,
  type ReactNode,
} from 'react';

interface LazyComponentProps {
  fallback?: ReactNode;
}

function DefaultFallback() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="skeleton-shimmer h-8 w-32 rounded" />
    </div>
  );
}

export function lazyLoad<TComponent extends ComponentType<any>>(
  importFn: () => Promise<{ default: TComponent }>,
  fallback?: ReactNode
) {
  type AnyComponent = ComponentType<any>;
  type Props = ComponentProps<TComponent>;

  const LazyComponent = lazy(
    importFn as unknown as () => Promise<{ default: AnyComponent }>
  ) as unknown as LazyExoticComponent<TComponent>;

  return function LazyWrapper(props: LazyComponentProps & Props) {
    const { fallback: fallbackProp, ...rest } = props as LazyComponentProps & Props;
    return (
      <Suspense fallback={fallbackProp ?? fallback ?? <DefaultFallback />}>
        <LazyComponent {...(rest as Props)} />
      </Suspense>
    );
  };
}

export const LazyChatbot = lazyLoad(
  () => import('@/components/chat/Chatbot').then((m) => ({ default: m.Chatbot }))
);

export const LazyCommandPalette = lazyLoad(
  () =>
    import('@/components/common/CommandPalette').then((m) => ({
      default: m.CommandPalette,
    }))
);
