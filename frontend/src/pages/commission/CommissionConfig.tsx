import { useEffect, useState } from 'react';
import { commissionApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';

interface ConfigItem {
  id: number;
  effective_month: string;
  agent_commission_rate: string;
  parent_commission_rate: string;
  company_commission_rate: string;
  status: number;
}

export default function CommissionConfig() {
  const [data, setData] = useState<ConfigItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await commissionApi.configPage({ page: 1, page_size: 50 });
      const result = res as unknown as { data: PageResult<ConfigItem> };
      setData(result.data.items || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-foreground">分润配置</h1>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="data-table">
          <thead className="bg-background-secondary">
            <tr>
              <th>生效月份</th>
              <th className="text-right">代理商比例</th>
              <th className="text-right">上级比例</th>
              <th className="text-right">公司比例</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={5} className="text-center py-8 text-foreground-muted">暂无配置</td></tr>
            ) : data.map(item => (
              <tr key={item.id} className="hover:bg-background-hover">
                <td className="font-medium">{item.effective_month}</td>
                <td className="text-right font-mono-num">{Number(item.agent_commission_rate || 0).toFixed(2)}%</td>
                <td className="text-right font-mono-num">{Number(item.parent_commission_rate || 0).toFixed(2)}%</td>
                <td className="text-right font-mono-num">{Number(item.company_commission_rate || 0).toFixed(2)}%</td>
                <td>
                  <span className={`px-2 py-0.5 rounded text-xs ${item.status === 0 ? 'bg-success/10 text-success' : 'bg-foreground-muted/10 text-foreground-muted'}`}>
                    {item.status === 0 ? '启用' : '禁用'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
