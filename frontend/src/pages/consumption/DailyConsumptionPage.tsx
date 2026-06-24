import { useEffect, useState } from 'react';
import { consumptionApi, customerApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';

interface DailyConsumption {
  id: number;
  customer_account_id: number;
  customer_name: string;
  data_date: string;
  data_month: string;
  total_consumption: string;
  hour_1: string; hour_2: string; hour_3: string; hour_4: string; hour_5: string; hour_6: string;
  hour_7: string; hour_8: string; hour_9: string; hour_10: string; hour_11: string; hour_12: string;
  hour_13: string; hour_14: string; hour_15: string; hour_16: string; hour_17: string; hour_18: string;
  hour_19: string; hour_20: string; hour_21: string; hour_22: string; hour_23: string; hour_24: string;
}

interface CustomerOption {
  id: number;
  customer_name: string;
}

const HOUR_KEYS = Array.from({ length: 24 }, (_, i) => `hour_${i + 1}`);

export default function DailyConsumptionPage() {
  const [data, setData] = useState<DailyConsumption[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [customerId, setCustomerId] = useState('');
  const [dataMonth, setDataMonth] = useState('');
  const [dataDate, setDataDate] = useState('');
  const [showHours, setShowHours] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<DailyConsumption | null>(null);
  const pageSize = 20;

  const emptyForm: Record<string, unknown> = {
    customer_account_id: '',
    data_date: '',
    total_consumption: '',
  };
  HOUR_KEYS.forEach(k => { emptyForm[k] = ''; });
  const [form, setForm] = useState<Record<string, unknown>>(emptyForm);

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
      const res = await consumptionApi.dailyPage(params);
      const result = res as unknown as { data: PageResult<DailyConsumption> };
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

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setModalOpen(true);
  };

  const openEdit = (item: DailyConsumption) => {
    setEditing(item);
    const next: Record<string, unknown> = {
      customer_account_id: item.customer_account_id,
      data_date: item.data_date,
      total_consumption: item.total_consumption,
    };
    HOUR_KEYS.forEach(k => { next[k] = (item as unknown as Record<string, unknown>)[k] || ''; });
    setForm(next);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload: Record<string, unknown> = {};
    Object.entries(form).forEach(([k, v]) => {
      payload[k] = v === '' ? undefined : (k === 'customer_account_id' ? Number(v) : (k.startsWith('hour_') || k === 'total_consumption') ? Number(v) : v);
    });
    try {
      if (editing) {
        await consumptionApi.dailyUpdate({ ...payload, id: editing.id });
      } else {
        await consumptionApi.dailyCreate(payload);
      }
      setModalOpen(false);
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : '操作失败');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确认删除？')) return;
    try {
      await consumptionApi.dailyDelete(id);
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : '删除失败');
    }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-foreground">日用电数据</h1>
        <button onClick={openCreate} className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">新增</button>
      </div>

      <div className="flex gap-3 items-center flex-wrap">
        <select value={customerId} onChange={e => { setCustomerId(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground">
          <option value="">全部客户</option>
          {customers.map(c => <option key={c.id} value={c.id}>{c.customer_name}</option>)}
        </select>
        <input type="month" value={dataMonth} onChange={e => { setDataMonth(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
        <input type="date" value={dataDate} onChange={e => { setDataDate(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
        <label className="flex items-center gap-2 text-sm text-foreground-secondary">
          <input type="checkbox" checked={showHours} onChange={e => setShowHours(e.target.checked)} />
          显示24小时明细
        </label>
        <button onClick={fetchData} className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">查询</button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="data-table">
          <thead className="bg-background-secondary">
            <tr>
              <th>客户</th>
              <th>日期</th>
              <th>月份</th>
              <th className="text-right">总电量</th>
              {showHours && HOUR_KEYS.map(k => <th key={k} className="text-right">{k.replace('hour_', 'H')}</th>)}
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={showHours ? 28 : 5} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={showHours ? 28 : 5} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
            ) : data.map(item => (
              <tr key={item.id} className="hover:bg-background-hover">
                <td className="font-medium">{item.customer_name}</td>
                <td>{item.data_date}</td>
                <td>{item.data_month}</td>
                <td className="text-right font-mono-num">{Number(item.total_consumption || 0).toFixed(2)}</td>
                {showHours && HOUR_KEYS.map(k => (
                  <td key={k} className="text-right font-mono-num">{Number((item as unknown as Record<string, unknown>)[k] || 0).toFixed(2)}</td>
                ))}
                <td>
                  <div className="flex gap-2">
                    <button onClick={() => openEdit(item)} className="text-accent text-sm hover:underline">编辑</button>
                    <button onClick={() => handleDelete(item.id)} className="text-danger text-sm hover:underline">删除</button>
                  </div>
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

      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-lg border border-border w-full max-w-3xl max-h-[90vh] overflow-auto">
            <div className="p-6 space-y-4">
              <h2 className="text-lg font-bold text-foreground">{editing ? '编辑日用电' : '新增日用电'}</h2>
              <form onSubmit={handleSubmit} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-foreground-secondary mb-1">客户</label>
                    <select required value={String(form.customer_account_id || '')} onChange={e => setForm({ ...form, customer_account_id: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground">
                      <option value="">请选择</option>
                      {customers.map(c => <option key={c.id} value={c.id}>{c.customer_name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-foreground-secondary mb-1">日期</label>
                    <input required type="date" value={String(form.data_date || '')} onChange={e => setForm({ ...form, data_date: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
                  </div>
                  <div>
                    <label className="block text-sm text-foreground-secondary mb-1">总电量</label>
                    <input required type="number" step="0.01" value={String(form.total_consumption || '')} onChange={e => setForm({ ...form, total_consumption: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-foreground-secondary mb-1">24小时电量</label>
                  <div className="grid grid-cols-6 gap-2">
                    {HOUR_KEYS.map(k => (
                      <input key={k} type="number" step="0.01" placeholder={k.replace('hour_', 'H')} value={String(form[k] || '')} onChange={e => setForm({ ...form, [k]: e.target.value })} className="px-2 py-1 rounded-md bg-background-secondary border border-border text-xs text-foreground" />
                    ))}
                  </div>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button type="button" onClick={() => setModalOpen(false)} className="px-4 py-1.5 rounded-md border border-border text-sm text-foreground-secondary">取消</button>
                  <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">保存</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
