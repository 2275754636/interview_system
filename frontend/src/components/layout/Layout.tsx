import { cn } from "@/lib/utils";

interface LayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
}

export function Layout({ children, sidebar }: LayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        {sidebar && (
          <aside className="hidden md:block w-64 border-r bg-card">
            {sidebar}
          </aside>
        )}

        <main className={cn(
          "flex-1 p-4",
          sidebar && "md:ml-0"
        )}>
          <div className="grid gap-4 auto-rows-min">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
