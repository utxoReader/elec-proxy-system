import { NavLink } from 'react-router-dom';
import { useTheme } from '@/shared/useTheme';
import { cn } from '@/shared/utils';
import {
  LayoutDashboard,
  Users,
  UserCircle,
  DollarSign,
  Zap,
  FileText,
  BarChart3,
  Percent,
  Sun,
  Moon,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const navItems = [
  { to: '/dashboard', label: '首页看板', icon: LayoutDashboard },
  { to: '/agents', label: '代理管理', icon: Users },
  { to: '/customers', label: '客户管理', icon: UserCircle },
  { to: '/prices', label: '电价管理', icon: DollarSign },
  { to: '/consumption', label: '用电数据', icon: Zap },
  { to: '/inquiries', label: '询价报价', icon: FileText },
  { to: '/profits', label: '利润管理', icon: BarChart3 },
  { to: '/commissions', label: '分润结算', icon: Percent },
];

interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

export function Sidebar({ collapsed = false, onToggle }: SidebarProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <aside
      className={cn(
        'flex flex-col border-r border-border bg-background-secondary transition-all duration-200',
        collapsed ? 'w-16' : 'w-56'
      )}
    >
      {/* Logo */}
      <div className="h-12 flex items-center px-4 border-b border-border justify-between">
        {!collapsed && (
          <h1 className="text-base font-bold text-foreground truncate">桐叶售电</h1>
        )}
        <button
          type="button"
          onClick={onToggle}
          className="flex h-7 w-7 items-center justify-center rounded-md text-foreground-secondary hover:bg-background-tertiary hover:text-foreground transition-colors"
          aria-label={collapsed ? '展开' : '收起'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg text-sm transition-colors',
                collapsed ? 'justify-center px-2 py-2' : 'px-3 py-2',
                isActive
                  ? 'bg-accent/10 text-accent font-medium'
                  : 'text-foreground-secondary hover:bg-background-tertiary hover:text-foreground'
              )
            }
            title={collapsed ? label : undefined}
          >
            <Icon className="w-4 h-4 shrink-0" />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Theme toggle */}
      <div className="p-2 border-t border-border">
        <button
          onClick={toggleTheme}
          className={cn(
            'flex items-center gap-3 rounded-lg text-sm text-foreground-secondary hover:bg-background-tertiary hover:text-foreground transition-colors',
            collapsed ? 'justify-center w-full px-2 py-2' : 'w-full px-3 py-2'
          )}
          title={collapsed ? (theme === 'dark' ? '浅色模式' : '深色模式') : undefined}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 shrink-0" /> : <Moon className="w-4 h-4 shrink-0" />}
          {!collapsed && <span>{theme === 'dark' ? '浅色模式' : '深色模式'}</span>}
        </button>
      </div>
    </aside>
  );
}
