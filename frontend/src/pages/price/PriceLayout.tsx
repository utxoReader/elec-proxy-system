import { NavLink, Outlet } from 'react-router-dom';

const tabs = [
  { to: '/prices/base', label: '分时电价' },
  { to: '/prices/grid', label: '电网电价' },
  { to: '/prices/wholesale', label: '批发价' },
  { to: '/prices/allocation', label: '市场分摊价' },
  { to: '/prices/other', label: '其他费用' },
];

export default function PriceLayout() {
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
