import { useEffect, useState } from 'react';
import { customerApi } from '@/shared/api';
import type { PageResult, CustomerStatus } from '@/shared/types';

interface CustomerContractItem {
  id: number;
  customer_name: string;
  customer_status: CustomerStatus;
  contract_start_date: string;
  contract_end_date: string;
  price_difference: string;
  agent_name: string;
}

export default function CustomerContract() {
  const [data, setData] = useState<CustomerContractItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [customerName, setCustomerName] = useState('');
  const [terminateModal, setTerminateModal] = useState<{ open: boolean; id: number | null; name: string }>({ open: false, id: null, name: '' });
  const [terminateDate, setTerminateDate] = useState('');
  const [renewModal, setRenewModal] = useState<{ open: boolean; id: number | null; name: string }>({ open: false, id: null, name: '' });
  const [renewStart, setRenewStart] = useState('');
  const [renewEnd, setRenewEnd] = useState('');
  const pageSize = 20;

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (customerName) params.customer_name = customerName;
      const res = await customerApi.page(params);
      const result = res as unknown as { data: PageResult<CustomerContractItem> };
      setData(result.data.items || []);
      setTotal(result.data.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page]);

  const handleTerminate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!terminateModal.id || !terminateDate) return;
    try {
      await customerApi.updateStatus(terminateModal.id, 'terminated');
      setTerminateModal({ open: false, id: null, name: '' });
      setTerminateDate('');
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : '终止失败');
    }
  };

  const handleRenew = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renewModal.id || !renewStart || !renewEnd) return;
    try {
      await customerApi.updatePriceAndContract({
        customer_account_id: renewModal.id,
        new_price_difference: 0,
        effective_date: renewStart,
        change_reason: '合同续签',
        new_contract_start_date: renewStart,
        new_contract_end_date: renewEnd,
      });
      setRenewModal({ open: false, id: null, name: '' });
      setRenewStart('');
      setRenewEnd('');
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : '续签失败');
    }
  };

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-foreground">合同管理</h1>

      <div className="flex gap-3 items-center">
        <input
          type="text"
          value={customerName}
          onChange={e => { setCustomerName(e.target.value); setPage(1); }}
          className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground"
          placeholder="客户名称"
        />
        <button onClick={fetchData} className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">
          查询
        </button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="data-table">
          <thead className="bg-background-secondary">
            <tr>
              <th>客户名称</th>
              <th>状态</th>
              <th>代理</th>
              <th>合同开始</th>
              <th>合同结束</th>
              <th>价差</th>
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
                <td>
                  <span className={`px-2 py-0.5 rounded text-xs ${item.customer_status === 'terminated' ? 'bg-danger/10 text-danger' : 'bg-accent/10 text-accent'}`}>
                    {item.customer_status === 'terminated' ? '已终止' : item.customer_status === 'contracted' ? '已签约' : '其他'}
                  </span>
                </td>
                <td>{item.agent_name || '-'}</td>
                <td>{item.contract_start_date || '-'}</td>
                <td>{item.contract_end_date || '-'}</td>
                <td className="text-right font-mono-num">{item.price_difference ?? '-'}</td>
                <td>
                  <div className="flex gap-2">
                    {item.customer_status !== 'terminated' && (
                      <>
                        <button onClick={() => setRenewModal({ open: true, id: item.id, name: item.customer_name })} className="text-accent text-sm hover:underline">续签</button>
                        <button onClick={() => setTerminateModal({ open: true, id: item.id, name: item.customer_name })} className="text-danger text-sm hover:underline">终止</button>
                      </>
                    )}
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

      {terminateModal.open && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-lg border border-border w-full max-w-sm p-6 space-y-4">
            <h2 className="text-lg font-bold text-foreground">终止合同</h2>
            <p className="text-sm text-foreground-secondary">客户：{terminateModal.name}</p>
            <form onSubmit={handleTerminate} className="space-y-3">
              <div>
                <label className="block text-sm text-foreground-secondary mb-1">终止日期</label>
                <input required type="date" value={terminateDate} onChange={e => setTerminateDate(e.target.value)} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setTerminateModal({ open: false, id: null, name: '' })} className="px-4 py-1.5 rounded-md border border-border text-sm text-foreground-secondary">取消</button>
                <button type="submit" className="px-4 py-1.5 rounded-md bg-danger text-white text-sm hover:opacity-90">确认终止</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {renewModal.open && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-lg border border-border w-full max-w-sm p-6 space-y-4">
            <h2 className="text-lg font-bold text-foreground">续签合同</h2>
            <p className="text-sm text-foreground-secondary">客户：{renewModal.name}</p>
            <form onSubmit={handleRenew} className="space-y-3">
              <div>
                <label className="block text-sm text-foreground-secondary mb-1">新合同开始</label>
                <input required type="date" value={renewStart} onChange={e => setRenewStart(e.target.value)} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
              </div>
              <div>
                <label className="block text-sm text-foreground-secondary mb-1">新合同结束</label>
                <input required type="date" value={renewEnd} onChange={e => setRenewEnd(e.target.value)} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setRenewModal({ open: false, id: null, name: '' })} className="px-4 py-1.5 rounded-md border border-border text-sm text-foreground-secondary">取消</button>
                <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">确认续签</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
