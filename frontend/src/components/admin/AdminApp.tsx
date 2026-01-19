import * as React from 'react';

import { Button } from '@/components/ui/button';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { LazyCommandPalette } from '@/lib/lazy';
import { useAdminStore, useCommandStore, useThemeStore } from '@/stores';
import { Shield, KeyRound, LayoutDashboard, Download, FlaskConical, ArrowLeft } from 'lucide-react';
import { AdminTokenDialog } from '@/components/admin/AdminTokenDialog';
import { OverviewPage } from '@/components/admin/pages/OverviewPage';
import { ExportPage } from '@/components/admin/pages/ExportPage';
import { ResearchPage } from '@/components/admin/pages/ResearchPage';

type AdminRoute = 'overview' | 'export' | 'research';

function parseAdminRoute(hash: string): AdminRoute {
  // hash examples: "admin", "admin/overview", "admin/export"
  const parts = hash.replace(/^#/, '').split('/');
  const route = parts[1] || 'overview';
  if (route === 'export' || route === 'research' || route === 'overview') return route;
  return 'overview';
}

function setHash(value: string) {
  window.location.hash = value ? `#${value}` : '';
}

export interface AdminAppProps {
  currentHash: string;
}

export function AdminApp({ currentHash }: AdminAppProps) {
  const route = React.useMemo(() => parseAdminRoute(currentHash), [currentHash]);
  const { token } = useAdminStore();
  const { isOpen, toggle, close } = useCommandStore();
  const { setMode } = useThemeStore();

  const [tokenOpen, setTokenOpen] = React.useState(false);

  const commands = [
    { id: 'theme-light', label: '浅色模式', shortcut: '⌘1', onSelect: () => setMode('light') },
    { id: 'theme-dark', label: '深色模式', shortcut: '⌘2', onSelect: () => setMode('dark') },
    { id: 'theme-system', label: '跟随系统', shortcut: '⌘3', onSelect: () => setMode('system') },
    { id: 'admin-overview', label: '监管概览', shortcut: 'G', onSelect: () => setHash('admin/overview') },
    { id: 'admin-export', label: '会话导出', shortcut: 'E', onSelect: () => setHash('admin/export') },
    { id: 'admin-research', label: '研究工具', shortcut: 'R', onSelect: () => setHash('admin/research') },
    { id: 'admin-token', label: '设置 Token', shortcut: 'T', onSelect: () => setTokenOpen(true) },
    { id: 'go-interview', label: '返回访谈', shortcut: 'Esc', onSelect: () => setHash('') },
  ];

  const content = route === 'export' ? <ExportPage /> : route === 'research' ? <ResearchPage /> : <OverviewPage />;

  return (
    <>
      <LazyCommandPalette
        isOpen={isOpen}
        onOpenChange={(open) => (open ? toggle() : close())}
        commands={commands}
        placeholder="搜索命令..."
      />

      <div className="flex min-h-screen flex-col fade-in">
        <Header
          title="后台监管仪表盘"
          subtitle="会话审计 · 指标可视化 · 研究工具"
          onCommandOpen={toggle}
          actions={
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setHash('')}
                className="gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span className="hidden sm:inline">返回访谈</span>
              </Button>
              <Button
                variant={token ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTokenOpen(true)}
                className="gap-2"
              >
                <KeyRound className="h-4 w-4" />
                <span className="hidden sm:inline">{token ? 'Token 已设置' : '设置 Token'}</span>
              </Button>
            </div>
          }
        />

        <div className="flex flex-1">
          <Sidebar>
            <div className="space-y-3">
              <div className="rounded-xl bg-card p-4 shadow-card card-interactive">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-primary" />
                  <h3 className="font-semibold">监管导航</h3>
                </div>
                <div className="mt-3 space-y-2">
                  <Button
                    variant={route === 'overview' ? 'default' : 'outline'}
                    className="w-full justify-start gap-2"
                    onClick={() => setHash('admin/overview')}
                  >
                    <LayoutDashboard className="h-4 w-4" />
                    概览
                  </Button>
                  <Button
                    variant={route === 'export' ? 'default' : 'outline'}
                    className="w-full justify-start gap-2"
                    onClick={() => setHash('admin/export')}
                  >
                    <Download className="h-4 w-4" />
                    导出
                  </Button>
                  <Button
                    variant={route === 'research' ? 'default' : 'outline'}
                    className="w-full justify-start gap-2"
                    onClick={() => setHash('admin/research')}
                  >
                    <FlaskConical className="h-4 w-4" />
                    研究工具
                  </Button>
                </div>
                <p className="mt-3 text-xs text-muted-foreground">
                  后端需配置 <code>ADMIN_TOKEN</code> 才会启用该模块。
                </p>
              </div>
            </div>
          </Sidebar>

          <main className="flex-1 p-4">
            <div className="mx-auto max-w-6xl">{content}</div>
          </main>
        </div>
      </div>

      {tokenOpen ? <AdminTokenDialog open={tokenOpen} onOpenChange={setTokenOpen} /> : null}
    </>
  );
}

