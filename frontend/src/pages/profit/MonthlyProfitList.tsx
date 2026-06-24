import { useEffect, useState } from 'react';
import { profitApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';

interface MonthlyProfit {
  id: number;
  customer_name: string;
  profit_month: string;
  total_consumption: string;
  total_profit: string;
  adjusted_total_profit: string;
  status: number;
  data_completeness_rate: string;
}

const STATUS_MAP: Record<number, string> = {
  1: '待计算', 2: '已调平', 4: '已确认', 5: '已结算',
};

export default function MonthlyProfitList() {
  const [data, setData] = useState<MonthlyProfit[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [profitMonth, setProfitMonth] = useState('');
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (profitMonth) params.profit_month = profitMonth;
      const res = await profitApi.monthlyProfitPage(params);
      const result = res as unknown as { data: PageResult<MonthlyProfit> };
      setData(result.data.items || []);
      setTotal(result.data.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page, profitMonth]);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-foreground">月度利润</h1>
      </div>

      {/* Filters */}
      <div className="flex gap-3 items-center">
        <input
          type="month"
          value={profitMonth}
          onChange={e => { setProfitMonth(e.target.value); setPage(1); }}
          className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground"
          placeholder="选择月份"
        />
        <button onClick={fetchData} className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">
          查询
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="data-table">
          <thead className="bg-background-secondary">
            <tr>
              <th>客户</th>
              <th>月份</th>
              <th className="text-right">用电量</th>
              <th className="text-right">总利润</th>
              <th className="text-right">调平后利润</th>
              <th className="text-right">完整率</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={8} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
            ) : data.map(item => (
              <tr key={item.id} className="hover:bg-background-hover">
                <td className="font-medium">{item.customer_name}</td>
                <td>{item.profit_month}</td>
                <td className="text-right font-mono-num">{Number(item.total_consumption).toFixed(2)}</td>
                <td className="text-right font-mono-num">{Number(item.total_profit).toFixed(2)}</td>
                <td className="text-right font-mono-num">{Number(item.adjusted_total_profit).toFixed(2)}</td>
                <td className="text-right">{Number(item.data_completeness_rate || 0).toFixed(1)}%</td>
                <td><span className="px-2 py-0.5 rounded text-xs bg-accent/10 text-accent">{STATUS_MAP[item.status] || '未知'}</span></td>
                <td>
                  <button className="text-accent text-sm hover:underline">详情</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center text-sm text-foreground-secondary">
        <span>共 {total} 条</span>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 rounded border border-border disabled:opacity-40">上一页</button>
          <span className="px-3 py-1">第 {page} 页</span>
          <button disabled={page * pageSize >= total} onClick={() => setPage(p => p + 1)} className="px-3 py-1 rounded border border-border disabled:opacity-40">下一页</button>
        </div>
      </div>
    </div>
  );
}
