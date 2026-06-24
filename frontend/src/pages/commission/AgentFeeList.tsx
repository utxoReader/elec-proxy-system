import { useEffect, useState } from 'react';
import { commissionApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';

interface AgentFee {
  id: number;
  agent_name: string;
  customer_name: string;
  fee_month: string;
  gross_profit: string;
  commission_amount: string;
  approval_status: number;
  settlement_status: number;
  net_amount: string;
}

const APPROVAL_MAP: Record<number, { label: string; color: string }> = {
  1: { label: '待审核', color: 'bg-warning/10 text-warning' },
  2: { label: '已审核', color: 'bg-success/10 text-success' },
  3: { label: '已驳回', color: 'bg-danger/10 text-danger' },
};

const SETTLEMENT_MAP: Record<number, string> = {
  1: '待结算', 2: '已结算', 3: '已支付',
};

export default function AgentFeeList() {
  const [data, setData] = useState<AgentFee[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [pageRes, statsRes] = await Promise.all([
        commissionApi.agentFeePage({ page: 1, page_size: 50 }),
        commissionApi.agentFeeStatistics(),
      ]);
      const pageResult = pageRes as unknown as { data: PageResult<AgentFee> };
      setData(pageResult.data.items || []);
      const statsResult = statsRes as unknown as { data: Record<string, unknown> };
      setStats(statsResult.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-foreground">代理费</h1>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-5 gap-3">
          {[
            { label: '总额', value: Number(stats.total_amount || 0).toFixed(2), color: '' },
            { label: '待审核', value: Number(stats.pending_approval_amount || 0).toFixed(2), color: 'text-warning' },
            { label: '已审核', value: Number(stats.approved_amount || 0).toFixed(2), color: 'text-success' },
            { label: '已结算', value: Number(stats.settled_amount || 0).toFixed(2), color: '' },
            { label: '已支付', value: Number(stats.paid_amount || 0).toFixed(2), color: '' },
          ].map(card => (
            <div key={card.label} className="rounded-lg border border-border bg-background-secondary p-3">
              <div className="text-xs text-foreground-secondary">{card.label}</div>
              <div className={`text-base font-bold font-mono-num mt-1 ${card.color}`}>{card.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="data-table">
          <thead className="bg-background-secondary">
            <tr>
              <th>代理</th>
              <th>客户</th>
              <th>月份</th>
              <th className="text-right">毛利润</th>
              <th className="text-right">佣金</th>
              <th className="text-right">净额</th>
              <th>审批</th>
              <th>结算</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={8} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
            ) : data.map(item => (
              <tr key={item.id} className="hover:bg-background-hover">
                <td className="font-medium">{item.agent_name}</td>
                <td>{item.customer_name}</td>
                <td>{item.fee_month}</td>
                <td className="text-right font-mono-num">{Number(item.gross_profit || 0).toFixed(2)}</td>
                <td className="text-right font-mono-num">{Number(item.commission_amount || 0).toFixed(2)}</td>
                <td className="text-right font-mono-num">{Number(item.net_amount || 0).toFixed(2)}</td>
                <td>
                  <span className={`px-2 py-0.5 rounded text-xs ${APPROVAL_MAP[item.approval_status]?.color || ''}`}>
                    {APPROVAL_MAP[item.approval_status]?.label || '未知'}
                  </span>
                </td>
                <td className="text-foreground-secondary text-sm">
                  {SETTLEMENT_MAP[item.settlement_status] || '未知'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
