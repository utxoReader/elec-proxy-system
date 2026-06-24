import { NavLink, Outlet } from 'react-router-dom';

const tabs = [
  { to: '/customers/list', label: '客户列表' },
  { to: '/customers/price-change', label: '价格变更' },
  { to: '/customers/contract', label: '合同管理' },
];

export default function CustomerLayout() {
  return (
    <div className="flex flex-col h-full">
      <div className="flex gap-1 px-6 pt-4 border-b border-border overflow-x-auto">
        {tabs.map(tab => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              `px-4 py-2 text-sm border-b-2 -mb-[1px] whitespace-nowrap transition-colors ${
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
