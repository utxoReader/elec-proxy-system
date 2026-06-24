import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { AppShell } from '@/shared/AppShell';
import { Sidebar } from '@/shared/Sidebar';
import { useAuth } from '@/shared/auth/useAuth';
import { Button } from '@/shared/ui/Button';
import { PanelLeft, LogOut, User } from 'lucide-react';

export function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const { logout } = useAuth();

  return (
    <AppShell>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} />
      <div className="flex flex-1 flex-col min-w-0">
        <header className="h-12 shrink-0 border-b border-border bg-background-secondary flex items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setCollapsed((v) => !v)}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-foreground-secondary hover:bg-background-tertiary hover:text-foreground transition-colors"
              aria-label={collapsed ? '展开侧边栏' : '收起侧边栏'}
            >
              <PanelLeft size={18} />
            </button>
            <span className="text-sm font-medium text-foreground">桐叶售电管理系统</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm text-foreground-secondary">
              <User size={16} />
              <span>管理员</span>
            </div>
            <Button variant="ghost" size="sm" onClick={logout} className="gap-1.5">
              <LogOut size={14} />
              退出
            </Button>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </AppShell>
  );
}
