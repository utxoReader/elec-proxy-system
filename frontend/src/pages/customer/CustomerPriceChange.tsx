import { useEffect, useState } from 'react';
import { customerApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';

interface PriceHistoryItem {
  id: number;
  customer_account_id: number;
  customer_name: string;
  old_price_difference: string;
  new_price_difference: string;
  effective_date: string;
  change_reason: string;
  created_at: string;
}

interface CustomerOption {
  id: number;
  customer_name: string;
}

export default function CustomerPriceChange() {
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [customerId, setCustomerId] = useState('');
  const [newPriceDifference, setNewPriceDifference] = useState('');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [changeReason, setChangeReason] = useState('');
  const [newContractStartDate, setNewContractStartDate] = useState('');
  const [newContractEndDate, setNewContractEndDate] = useState('');
  const [history, setHistory] = useState<PriceHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const fetchCustomers = async () => {
    try {
      const res = await customerApi.simpleList();
      setCustomers(((res as unknown as { data: CustomerOption[] }).data) || []);
    } catch {
      setCustomers([]);
    }
  };

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (customerId) params.customer_account_id = Number(customerId);
      const res = await customerApi.priceHistoryPage(params);
      const result = res as unknown as { data: PageResult<PriceHistoryItem> };
      setHistory(result.data.items || []);
      setTotal(result.data.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
    fetchHistory();
  }, [page]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerId || !newPriceDifference || !effectiveDate) {
      alert('请填写必填项');
      return;
    }
    try {
      await customerApi.updatePriceAndContract({
        customer_account_id: Number(customerId),
        new_price_difference: Number(newPriceDifference),
        effective_date: effectiveDate,
        change_reason: changeReason,
        new_contract_start_date: newContractStartDate || undefined,
        new_contract_end_date: newContractEndDate || undefined,
      });
      setNewPriceDifference('');
      setEffectiveDate('');
      setChangeReason('');
      setNewContractStartDate('');
      setNewContractEndDate('');
      fetchHistory();
    } catch (err) {
      alert(err instanceof Error ? err.message : '价格变更失败');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-bold text-foreground">价格变更</h1>

      <form onSubmit={handleSubmit} className="p-4 rounded-lg border border-border bg-background-secondary space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">客户 <span className="text-danger">*</span></label>
            <select required value={customerId} onChange={e => setCustomerId(e.target.value)} className="w-full px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground">
              <option value="">请选择</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.customer_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">新价差 <span className="text-danger">*</span></label>
            <input required type="number" step="0.0001" value={newPriceDifference} onChange={e => setNewPriceDifference(e.target.value)} className="w-full px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">生效日期 <span className="text-danger">*</span></label>
            <input required type="date" value={effectiveDate} onChange={e => setEffectiveDate(e.target.value)} className="w-full px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">新合同开始</label>
            <input type="date" value={newContractStartDate} onChange={e => setNewContractStartDate(e.target.value)} className="w-full px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">新合同结束</label>
            <input type="date" value={newContractEndDate} onChange={e => setNewContractEndDate(e.target.value)} className="w-full px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">变更原因</label>
            <input value={changeReason} onChange={e => setChangeReason(e.target.value)} className="w-full px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          </div>
        </div>
        <div className="flex justify-end">
          <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">提交变更</button>
        </div>
      </form>

      <div className="space-y-3">
        <h2 className="text-base font-semibold text-foreground">变更历史</h2>
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="data-table">
            <thead className="bg-background-secondary">
              <tr>
                <th>客户</th>
                <th className="text-right">原价差</th>
                <th className="text-right">新价差</th>
                <th>生效日期</th>
                <th>变更原因</th>
                <th>操作时间</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
              ) : history.length === 0 ? (
                <tr><td colSpan={6} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
              ) : history.map(item => (
                <tr key={item.id} className="hover:bg-background-hover">
                  <td>{item.customer_name}</td>
                  <td className="text-right font-mono-num">{item.old_price_difference}</td>
                  <td className="text-right font-mono-num">{item.new_price_difference}</td>
                  <td>{item.effective_date}</td>
                  <td>{item.change_reason || '-'}</td>
                  <td>{item.created_at}</td>
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
    </div>
  );
}
