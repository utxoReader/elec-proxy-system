import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { inquiryApi, agentApi } from '@/shared/api';
import type { PageResult, InquiryStatus } from '@/shared/types';

interface Inquiry {
  id: number;
  customer_name: string;
  usage_month: string;
  estimated_monthly_consumption: string;
  inquiry_status: InquiryStatus;
  package_type: string;
  agent_name: string;
  created_at: string;
  quoted_price_difference: string;
}

const STATUS_MAP: Record<InquiryStatus, string> = {
  pending: '待处理',
  processing: '处理中',
  quoted: '已报价',
  cooperated: '已合作',
  rejected: '已拒绝',
  expired: '已过期',
};

const STATUS_COLOR: Record<InquiryStatus, string> = {
  pending: 'bg-warning/10 text-warning',
  processing: 'bg-accent/10 text-accent',
  quoted: 'bg-accent/10 text-accent',
  cooperated: 'bg-success/10 text-success',
  rejected: 'bg-danger/10 text-danger',
  expired: 'bg-foreground-muted/10 text-foreground-muted',
};

const STATUS_OPTIONS: { value: InquiryStatus | ''; label: string }[] = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '待处理' },
  { value: 'processing', label: '处理中' },
  { value: 'quoted', label: '已报价' },
  { value: 'cooperated', label: '已合作' },
  { value: 'rejected', label: '已拒绝' },
  { value: 'expired', label: '已过期' },
];

export default function InquiryList() {
  const navigate = useNavigate();
  const [data, setData] = useState<Inquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [inquiryStatus, setInquiryStatus] = useState<InquiryStatus | ''>('');
  const [customerName, setCustomerName] = useState('');
  const [usageMonth, setUsageMonth] = useState('');
  const [agents, setAgents] = useState<Record<string, unknown>[]>([]);
  const [agentId, setAgentId] = useState('');
  const pageSize = 20;

  const fetchAgents = async () => {
    try {
      const res = await agentApi.list();
      setAgents((res as unknown as { data: Record<string, unknown>[] }).data || []);
    } catch {
      setAgents([]);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (inquiryStatus) params.inquiry_status = inquiryStatus;
      if (customerName) params.customer_name = customerName;
      if (usageMonth) params.usage_month = usageMonth;
      if (agentId) params.agent_id = Number(agentId);
      const res = await inquiryApi.page(params);
      const result = res as unknown as { data: PageResult<Inquiry> };
      setData(result.data.items || []);
      setTotal(result.data.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
    fetchData();
  }, [page]);

  const handleExport = () => {
    window.open(inquiryApi.export(), '_blank');
  };

  const handleReject = async (id: number) => {
    const reason = prompt('请输入拒绝原因');
    if (reason === null) return;
    try {
      await inquiryApi.reject(id, reason);
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : '拒绝失败');
    }
  };

  const handleAccept = async (id: number) => {
    if (!confirm('确认接受报价？')) return;
    try {
      await inquiryApi.accept(id);
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : '接受失败');
    }
  };

  const handleTerminate = async (id: number) => {
    const date = prompt('请输入终止日期');
    if (!date) return;
    try {
      await inquiryApi.terminate(id, date);
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : '终止失败');
    }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-foreground">询价列表</h1>
        <div className="flex gap-2">
          <button onClick={handleExport} className="px-4 py-1.5 rounded-md border border-border text-sm text-foreground-secondary hover:bg-background-secondary">导出Excel</button>
          <button onClick={() => navigate('/inquiries/create')} className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">新建询价</button>
        </div>
      </div>

      <div className="flex gap-3 items-center flex-wrap">
        <input
          type="text"
          value={customerName}
          onChange={e => { setCustomerName(e.target.value); setPage(1); }}
          className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground"
          placeholder="客户名称"
        />
        <select
          value={inquiryStatus}
          onChange={e => { setInquiryStatus(e.target.value as InquiryStatus | ''); setPage(1); }}
          className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground"
        >
          {STATUS_OPTIONS.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
        </select>
        <input type="month" value={usageMonth} onChange={e => { setUsageMonth(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
        <select value={agentId} onChange={e => { setAgentId(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground">
          <option value="">全部代理</option>
          {agents.map((a: Record<string, unknown>) => (
            <option key={String(a.id)} value={String(a.id)}>{String(a.agent_name || a.name || '')}</option>
          ))}
        </select>
        <button onClick={fetchData} className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">查询</button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="data-table">
          <thead className="bg-background-secondary">
            <tr>
              <th>客户</th>
              <th>月份</th>
              <th>套餐</th>
              <th className="text-right">预估用电量</th>
              <th className="text-right">报价价差</th>
              <th>状态</th>
              <th>代理</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={9} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
            ) : data.map(item => (
              <tr key={item.id} className="hover:bg-background-hover">
                <td className="font-medium">{item.customer_name}</td>
                <td>{item.usage_month}</td>
                <td>{item.package_type || '-'}</td>
                <td className="text-right font-mono-num">{Number(item.estimated_monthly_consumption || 0).toFixed(2)}</td>
                <td className="text-right font-mono-num">{item.quoted_price_difference ?? '-'}</td>
                <td><span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLOR[item.inquiry_status]}`}>{STATUS_MAP[item.inquiry_status]}</span></td>
                <td>{item.agent_name || '-'}</td>
                <td>{item.created_at || '-'}</td>
                <td>
                  <div className="flex gap-2 flex-wrap">
                    <button onClick={() => navigate(`/inquiries/${item.id}`)} className="text-accent text-sm hover:underline">详情</button>
                    {item.inquiry_status === 'pending' && <button onClick={() => navigate(`/inquiries/${item.id}`)} className="text-accent text-sm hover:underline">报价</button>}
                    {item.inquiry_status === 'quoted' && <button onClick={() => handleAccept(item.id)} className="text-success text-sm hover:underline">接受</button>}
                    {(item.inquiry_status === 'pending' || item.inquiry_status === 'quoted') && <button onClick={() => handleReject(item.id)} className="text-danger text-sm hover:underline">拒绝</button>}
                    {item.inquiry_status === 'cooperated' && <button onClick={() => handleTerminate(item.id)} className="text-danger text-sm hover:underline">终止</button>}
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
    </div>
  );
}
