import { NavLink, Outlet } from 'react-router-dom';

const tabs = [
  { to: '/commissions/config', label: '分润配置' },
  { to: '/commissions/fees', label: '代理费' },
  { to: '/commissions/approval', label: '审批管理' },
];

export default function CommissionLayout() {
  return (
    <div className="flex flex-col h-full">
      <div className="flex gap-1 px-6 pt-4 border-b border-border">
        {tabs.map(tab => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              `px-4 py-2 text-sm border-b-2 -mb-[1px] transition-colors ${
                isActive
                  ? 'border-accent text-accent font-medium'
                  : 'border-transparent text-foreground-secondary hover:text-foreground'
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </div>
      <div className="flex-1 overflow-auto">
        <Outlet />
      </div>
    </div>
  );
}
