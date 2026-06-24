import { useEffect, useState } from 'react';
import { consumptionApi, customerApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';

interface HourlyConsumption {
  id: number;
  customer_account_id: number;
  customer_name: string;
  data_date: string;
  data_month: string;
  hour_index: number;
  consumption_value: string;
  time_period: string;
}

interface CustomerOption {
  id: number;
  customer_name: string;
}

export default function HourlyConsumptionPage() {
  const [data, setData] = useState<HourlyConsumption[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [customerId, setCustomerId] = useState('');
  const [dataMonth, setDataMonth] = useState('');
  const [dataDate, setDataDate] = useState('');
  const pageSize = 20;

  const fetchCustomers = async () => {
    try {
      const res = await customerApi.simpleList();
      setCustomers(((res as unknown as { data: CustomerOption[] }).data) || []);
    } catch {
      setCustomers([]);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (customerId) params.customer_account_id = Number(customerId);
      if (dataMonth) params.data_month = dataMonth;
      if (dataDate) params.data_date = dataDate;
      const res = await consumptionApi.hourlyPage(params);
      const result = res as unknown as { data: PageResult<HourlyConsumption> };
      setData(result.data.items || []);
      setTotal(result.data.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
    fetchData();
  }, [page]);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-foreground">小时用电</h1>

      <div className="flex gap-3 items-center flex-wrap">
        <select value={customerId} onChange={e => { setCustomerId(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground">
          <option value="">全部客户</option>
          {customers.map(c => <option key={c.id} value={c.id}>{c.customer_name}</option>)}
        </select>
        <input type="month" value={dataMonth} onChange={e => { setDataMonth(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
        <input type="date" value={dataDate} onChange={e => { setDataDate(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
        <button onClick={fetchData} className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">查询</button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="data-table">
          <thead className="bg-background-secondary">
            <tr>
              <th>客户</th>
              <th>日期</th>
              <th>月份</th>
              <th>时段</th>
              <th className="text-right">用电量</th>
              <th>峰平谷</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
            ) : data.map(item => (
              <tr key={item.id} className="hover:bg-background-hover">
                <td className="font-medium">{item.customer_name}</td>
                <td>{item.data_date}</td>
                <td>{item.data_month}</td>
                <td>{item.hour_index}</td>
                <td className="text-right font-mono-num">{Number(item.consumption_value || 0).toFixed(2)}</td>
                <td>{item.time_period || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

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
