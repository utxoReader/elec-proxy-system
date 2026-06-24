import { useEffect, useMemo, useState } from 'react';
import { commissionApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Modal } from '@/shared/ui/Modal';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/Card';
import { cn } from '@/shared/utils';
import { AlertCircle, CheckCircle, XCircle, RotateCcw, Coins } from 'lucide-react';

interface AgentFee {
  id: number;
  agent_name: string;
  customer_name: string;
  fee_month: string;
  gross_profit: string | number | null;
  commission_amount: string | number | null;
  net_amount: string | number | null;
  approval_status: number;
  settlement_status: number;
}

const APPROVAL_MAP: Record<number, { label: string; color: string }> = {
  1: { label: '待审核', color: 'bg-warning/10 text-warning' },
  2: { label: '已通过', color: 'bg-success/10 text-success' },
  3: { label: '已驳回', color: 'bg-danger/10 text-danger' },
};

const SETTLEMENT_MAP: Record<number, { label: string; color: string }> = {
  1: { label: '待结算', color: 'bg-warning/10 text-warning' },
  2: { label: '已结算', color: 'bg-success/10 text-success' },
  3: { label: '已支付', color: 'bg-accent/10 text-accent' },
};

type BatchAction = 'approve' | 'reject' | 'settle' | null;

export default function CommissionApproval() {
  const [data, setData] = useState<AgentFee[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [agentName, setAgentName] = useState('');
  const [feeMonth, setFeeMonth] = useState('');
  const [approvalStatus, setApprovalStatus] = useState('1');
  const pageSize = 20;

  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [batchAction, setBatchAction] = useState<BatchAction>(null);
  const [remark, setRemark] = useState('');

  const showMessage = (message: string, type: 'success' | 'error') => {
    if (type === 'success') {
      setSuccess(message);
      setError(null);
    } else {
      setError(message);
      setSuccess(null);
    }
    setTimeout(() => {
      setSuccess(null);
      setError(null);
    }, 4000);
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (agentName.trim()) params.agent_name = agentName.trim();
      if (feeMonth) params.fee_month = feeMonth;
      if (approvalStatus) params.approval_status = Number(approvalStatus);
      const res = (await commissionApi.agentFeePage(params)) as unknown as {
        success: boolean;
        data?: PageResult<AgentFee>;
        message?: string;
      };
      if (!res.success) throw new Error(res.message || '加载失败');
      const items = res.data?.items || [];
      setData(items);
      setTotal(res.data?.total || 0);
      setSelectedIds((prev) => prev.filter((id) => items.some((i) => i.id === id)));
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '加载代理费失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, approvalStatus]);

  const handleSearch = () => {
    setPage(1);
    fetchData();
  };

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const toggleAll = () => {
    const pageIds = data.map((i) => i.id);
    const allSelected = pageIds.every((id) => selectedIds.includes(id));
    if (allSelected) {
      setSelectedIds((prev) => prev.filter((id) => !pageIds.includes(id)));
    } else {
      setSelectedIds((prev) => Array.from(new Set([...prev, ...pageIds])));
    }
  };

  const submitBatch = async () => {
    if (!batchAction || selectedIds.length === 0) return;
    setActionLoading(true);
    try {
      let res: { success: boolean; message?: string } = { success: false };
      if (batchAction === 'approve') {
        res = (await commissionApi.batchApprove(selectedIds, 2, remark)) as unknown as typeof res;
      } else if (batchAction === 'reject') {
        res = (await commissionApi.batchApprove(selectedIds, 3, remark)) as unknown as typeof res;
      } else if (batchAction === 'settle') {
        res = (await commissionApi.batchSettle(selectedIds, remark)) as unknown as typeof res;
      }
      if (!res.success) throw new Error(res.message || '操作失败');
      showMessage(
        batchAction === 'approve'
          ? `已通过 ${selectedIds.length} 条记录`
          : batchAction === 'reject'
            ? `已驳回 ${selectedIds.length} 条记录`
            : `已结算 ${selectedIds.length} 条记录`,
        'success'
      );
      setBatchAction(null);
      setRemark('');
      setSelectedIds([]);
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '操作失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const modalTitle = useMemo(() => {
    switch (batchAction) {
      case 'approve':
        return '批量通过';
      case 'reject':
        return '批量驳回';
      case 'settle':
        return '批量结算';
      default:
        return '';
    }
  }, [batchAction]);

  return (
    <div className="p-6 space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>审批管理</CardTitle>
          <div className="flex items-center gap-2 text-sm text-foreground-secondary">
            已选 <span className="font-medium text-foreground">{selectedIds.length}</span> 条
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">
              <AlertCircle size={16} />
              {error}
            </div>
          )}
          {success && (
            <div className="flex items-center gap-2 rounded-lg border border-success/20 bg-success/10 px-4 py-3 text-sm text-success">
              <RotateCcw size={16} />
              {success}
            </div>
          )}

          <div className="flex flex-wrap items-end gap-3">
            <Input
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              placeholder="代理商名称"
              className="w-48"
            />
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">月份</label>
              <input
                type="month"
                value={feeMonth}
                onChange={(e) => setFeeMonth(e.target.value)}
                className={cn(
                  'flex h-10 w-40 rounded-lg border px-3 py-2 text-sm',
                  'bg-background-tertiary text-foreground',
                  'border-transparent placeholder:text-foreground-tertiary',
                  'transition-all duration-200 focus:outline-none focus:border-foreground'
                )}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">审批状态</label>
              <select
                value={approvalStatus}
                onChange={(e) => { setApprovalStatus(e.target.value); setPage(1); }}
                className={cn(
                  'flex h-10 w-32 rounded-lg border px-3 py-2 text-sm',
                  'bg-background-tertiary text-foreground',
                  'border-transparent focus:outline-none focus:border-foreground'
                )}
              >
                <option value="1">待审核</option>
                <option value="2">已通过</option>
                <option value="3">已驳回</option>
                <option value="">全部</option>
              </select>
            </div>
            <Button onClick={handleSearch}>查询</Button>
            {selectedIds.length > 0 && (
              <>
                <Button variant="success" size="sm" onClick={() => setBatchAction('approve')}>
                  <CheckCircle size={16} />
                  通过
                </Button>
                <Button variant="danger" size="sm" onClick={() => setBatchAction('reject')}>
                  <XCircle size={16} />
                  驳回
                </Button>
                <Button variant="accent" size="sm" onClick={() => setBatchAction('settle')}>
                  <Coins size={16} />
                  结算
                </Button>
              </>
            )}
          </div>

          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="data-table">
              <thead className="bg-background-tertiary">
                <tr>
                  <th className="w-10">
                    <input
                      type="checkbox"
                      checked={data.length > 0 && data.every((i) => selectedIds.includes(i.id))}
                      onChange={toggleAll}
                      className="rounded border-border bg-background-tertiary text-accent"
                    />
                  </th>
                  <th>代理</th>
                  <th>客户</th>
                  <th>月份</th>
                  <th className="text-right">毛利润</th>
                  <th className="text-right">佣金</th>
                  <th className="text-right">净额</th>
                  <th>审批状态</th>
                  <th>结算状态</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={9} className="text-center py-8 text-foreground-muted">加载中...</td>
                  </tr>
                ) : data.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center py-8 text-foreground-muted">暂无数据</td>
                  </tr>
                ) : (
                  data.map((item) => {
                    const approval = APPROVAL_MAP[item.approval_status] || { label: '未知', color: 'bg-foreground/10 text-foreground' };
                    const settlement = SETTLEMENT_MAP[item.settlement_status] || { label: '未知', color: 'bg-foreground/10 text-foreground' };
                    return (
                      <tr key={item.id} className="hover:bg-background-hover">
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedIds.includes(item.id)}
                            onChange={() => toggleSelect(item.id)}
                            className="rounded border-border bg-background-tertiary text-accent"
                          />
                        </td>
                        <td className="font-medium">{item.agent_name}</td>
                        <td>{item.customer_name}</td>
                        <td>{item.fee_month}</td>
                        <td className="text-right font-mono-num">{Number(item.gross_profit || 0).toFixed(2)}</td>
                        <td className="text-right font-mono-num">{Number(item.commission_amount || 0).toFixed(2)}</td>
                        <td className="text-right font-mono-num">{Number(item.net_amount || 0).toFixed(2)}</td>
                        <td>
                          <span className={cn('px-2 py-0.5 rounded text-xs', approval.color)}>{approval.label}</span>
                        </td>
                        <td>
                          <span className={cn('px-2 py-0.5 rounded text-xs', settlement.color)}>{settlement.label}</span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="flex justify-between items-center text-sm text-foreground-secondary">
            <span>共 {total} 条</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 rounded border border-border disabled:opacity-40"
              >
                上一页
              </button>
              <span className="px-3 py-1">第 {page} 页</span>
              <button
                disabled={page * pageSize >= total}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 rounded border border-border disabled:opacity-40"
              >
                下一页
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Modal
        open={!!batchAction}
        onClose={() => { setBatchAction(null); setRemark(''); }}
        title={modalTitle}
        description={`将对 ${selectedIds.length} 条记录执行「${modalTitle}」操作。`}
        footer={
          <>
            <Button variant="ghost" onClick={() => { setBatchAction(null); setRemark(''); }} disabled={actionLoading}>
              取消
            </Button>
            <Button
              variant={batchAction === 'reject' ? 'danger' : batchAction === 'settle' ? 'accent' : 'success'}
              onClick={submitBatch}
              isLoading={actionLoading}
            >
              确认
            </Button>
          </>
        }
      >
        <Input
          label="备注"
          value={remark}
          onChange={(e) => setRemark(e.target.value)}
          placeholder="可选备注"
        />
      </Modal>
    </div>
  );
}
