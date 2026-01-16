import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Menu } from "lucide-react";
import { cn } from "@/lib/utils";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";

interface SidebarProps {
  children: React.ReactNode;
  isOpen?: boolean;
  onToggle?: () => void;
}

export function Sidebar({ children, isOpen, onToggle }: SidebarProps) {
  return (
    <>
      <div className="md:hidden">
        <Sheet open={isOpen} onOpenChange={onToggle}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <VisuallyHidden>
              <SheetTitle>Navigation Menu</SheetTitle>
              <SheetDescription>Access navigation and settings</SheetDescription>
            </VisuallyHidden>
            <div className="h-full overflow-auto">
              {children}
            </div>
          </SheetContent>
        </Sheet>
      </div>

      <aside className={cn(
        "hidden md:block w-64 border-r bg-card",
        "h-[calc(100vh-4rem)] sticky top-16 overflow-auto"
      )}>
        <div className="p-6">
          {children}
        </div>
      </aside>
    </>
  );
}
