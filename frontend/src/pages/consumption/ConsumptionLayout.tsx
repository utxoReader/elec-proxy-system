import { NavLink, Outlet } from 'react-router-dom';

const tabs = [
  { to: '/consumption/daily', label: '日用电数据' },
  { to: '/consumption/hourly', label: '小时用电' },
  { to: '/consumption/point96', label: '96点数据' },
  { to: '/consumption/conversion', label: '数据转换' },
  { to: '/consumption/template', label: '曲线模板' },
  { to: '/consumption/import-task', label: '导入任务' },
];

export default function ConsumptionLayout() {
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
