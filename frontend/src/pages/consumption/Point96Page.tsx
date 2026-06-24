import { useEffect, useState, useRef } from 'react';
import { consumptionApi, customerApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';

interface Point96 {
  id: number;
  customer_account_id: number;
  customer_name: string;
  data_date: string;
  data_month: string;
  file_name: string;
  status: string;
  created_at: string;
}

interface CustomerOption {
  id: number;
  customer_name: string;
}

export default function Point96Page() {
  const [data, setData] = useState<Point96[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [customerId, setCustomerId] = useState('');
  const [dataMonth, setDataMonth] = useState('');
  const [dataDate, setDataDate] = useState('');
  const [importCustomerId, setImportCustomerId] = useState('');
  const [importDate, setImportDate] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
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
      const res = await consumptionApi.point96Page(params);
      const result = res as unknown as { data: PageResult<Point96> };
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

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file || !importCustomerId || !importDate) {
      alert('请选择客户、日期和文件');
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    formData.append('customer_account_id', importCustomerId);
    formData.append('data_date', importDate);
    try {
      const res = await consumptionApi.point96Import(formData);
      if (!res.ok) throw new Error('导入失败');
      alert('导入成功');
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : '导入失败');
    }
  };

  const handleConvert = async (id: number) => {
    if (!confirm('确认转换为日用电数据？')) return;
    try {
      await consumptionApi.point96ConvertToDaily(id);
      alert('转换成功');
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : '转换失败');
    }
  };

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-foreground">96点数据</h1>

      <form onSubmit={handleImport} className="p-4 rounded-lg border border-border bg-background-secondary space-y-3">
        <h2 className="text-sm font-semibold text-foreground">导入96点数据</h2>
        <div className="flex gap-3 items-end flex-wrap">
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">客户</label>
            <select required value={importCustomerId} onChange={e => setImportCustomerId(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground">
              <option value="">请选择</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.customer_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">日期</label>
            <input required type="date" value={importDate} onChange={e => setImportDate(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">文件</label>
            <input ref={fileRef} required type="file" accept=".xlsx,.xls,.csv" className="text-sm text-foreground" />
          </div>
          <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">导入</button>
        </div>
      </form>

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
              <th>文件名</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
            ) : data.map(item => (
              <tr key={item.id} className="hover:bg-background-hover">
                <td className="font-medium">{item.customer_name}</td>
                <td>{item.data_date}</td>
                <td>{item.data_month}</td>
                <td>{item.file_name || '-'}</td>
                <td>{item.status || '-'}</td>
                <td>{item.created_at || '-'}</td>
                <td>
                  <button onClick={() => handleConvert(item.id)} className="text-accent text-sm hover:underline">转日用电</button>
                </td>
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
