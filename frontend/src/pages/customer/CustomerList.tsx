import { useEffect, useMemo, useState } from 'react';
import { customerApi, agentApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { DatePicker } from '@/shared/ui/DatePicker';
import { Modal } from '@/shared/ui/Modal';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/Card';
import { cn } from '@/shared/utils';
import { Plus, Pencil, Trash2, AlertCircle, RotateCcw } from 'lucide-react';

interface Customer {
  id: number;
  customer_name: string;
  customer_code: string | null;
  customer_status: number;
  agent_id: number | null;
  agent_name: string | null;
  contract_start_date: string | null;
  contract_end_date: string | null;
  price_difference: string | number | null;
  voltage_level: string | null;
  contact_person: string | null;
  contact_phone: string | null;
}

interface AgentOption {
  id: number;
  name: string;
}

const STATUS_MAP: Record<number, { label: string; color: string }> = {
  1: { label: '待注册', color: 'bg-warning/10 text-warning' },
  2: { label: '待签约', color: 'bg-accent/10 text-accent' },
  3: { label: '已签约', color: 'bg-success/10 text-success' },
  4: { label: '已终止', color: 'bg-danger/10 text-danger' },
  5: { label: '已终止', color: 'bg-danger/10 text-danger' },
};

const STATUS_OPTIONS = [
  { value: '', label: '全部状态' },
  { value: '1', label: '待注册' },
  { value: '2', label: '待签约' },
  { value: '3', label: '已签约' },
  { value: '4', label: '已终止' },
];

const FORM_STATUS_OPTIONS = [
  { value: '1', label: '待注册' },
  { value: '2', label: '待签约' },
  { value: '3', label: '已签约' },
  { value: '4', label: '已终止' },
];

type CustomerFormData = {
  customer_name: string;
  customer_code: string;
  customer_status: string;
  agent_id: string;
  voltage_level: string;
  contact_person: string;
  contact_phone: string;
  price_difference: string;
  contract_start_date: string;
  contract_end_date: string;
};

const emptyForm: CustomerFormData = {
  customer_name: '',
  customer_code: '',
  customer_status: '2',
  agent_id: '',
  voltage_level: '',
  contact_person: '',
  contact_phone: '',
  price_difference: '',
  contract_start_date: '',
  contract_end_date: '',
};

function customerToForm(c: Customer): CustomerFormData {
  return {
    customer_name: c.customer_name,
    customer_code: c.customer_code || '',
    customer_status: String(c.customer_status || 2),
    agent_id: c.agent_id ? String(c.agent_id) : '',
    voltage_level: c.voltage_level || '',
    contact_person: c.contact_person || '',
    contact_phone: c.contact_phone || '',
    price_difference: c.price_difference !== null ? String(c.price_difference) : '',
    contract_start_date: c.contract_start_date || '',
    contract_end_date: c.contract_end_date || '',
  };
}

function formToPayload(data: CustomerFormData): Record<string, unknown> {
  return {
    customer_name: data.customer_name.trim(),
    customer_code: data.customer_code.trim() || null,
    customer_status: Number(data.customer_status),
    agent_id: data.agent_id ? Number(data.agent_id) : null,
    voltage_level: data.voltage_level.trim() || null,
    contact_person: data.contact_person.trim() || null,
    contact_phone: data.contact_phone.trim() || null,
    price_difference: data.price_difference ? Number(data.price_difference) : null,
    contract_start_date: data.contract_start_date || null,
    contract_end_date: data.contract_end_date || null,
  };
}

export default function CustomerList() {
  const [data, setData] = useState<Customer[]>([]);
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const [customerName, setCustomerName] = useState('');
  const [customerStatus, setCustomerStatus] = useState('');
  const [agentId, setAgentId] = useState('');

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState<CustomerFormData>(emptyForm);
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof CustomerFormData, string>>>({});

  const [deleteTarget, setDeleteTarget] = useState<Customer | null>(null);

  const agentFilterOptions = useMemo(
    () => [{ value: '', label: '全部代理' }, ...agents.map((a) => ({ value: String(a.id), label: a.name }))],
    [agents]
  );
  const agentFormOptions = useMemo(
    () => [{ value: '', label: '请选择代理' }, ...agents.map((a) => ({ value: String(a.id), label: a.name }))],
    [agents]
  );

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

  const fetchAgents = async () => {
    try {
      const res = (await agentApi.list()) as unknown as { success: boolean; data?: AgentOption[] };
      setAgents(res.data || []);
    } catch (err) {
      setAgents([]);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (customerName.trim()) params.customer_name = customerName.trim();
      if (customerStatus) params.customer_status = Number(customerStatus);
      if (agentId) params.agent_id = Number(agentId);
      const res = (await customerApi.page(params)) as unknown as { success: boolean; data?: PageResult<Customer>; message?: string };
      if (!res.success) throw new Error(res.message || '加载失败');
      setData(res.data?.items || []);
      setTotal(res.data?.total || 0);
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '加载客户列表失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  useEffect(() => {
    fetchData();
  }, [page]);

  const handleSearch = () => {
    setPage(1);
    fetchData();
  };

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setFormErrors({});
    setModalOpen(true);
  };

  const openEdit = (item: Customer) => {
    setEditing(item);
    setForm(customerToForm(item));
    setFormErrors({});
    setModalOpen(true);
  };

  const validate = (): boolean => {
    const errors: Partial<Record<keyof CustomerFormData, string>> = {};
    if (!form.customer_name.trim()) errors.customer_name = '客户名称不能为空';
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    setActionLoading(true);
    try {
      const payload = formToPayload(form);
      if (editing) {
        const res = (await customerApi.update({ id: editing.id, ...payload })) as unknown as {
          success: boolean;
          message?: string;
        };
        if (!res.success) throw new Error(res.message || '更新失败');
        showMessage('客户更新成功', 'success');
      } else {
        const res = (await customerApi.create(payload)) as unknown as {
          success: boolean;
          message?: string;
        };
        if (!res.success) throw new Error(res.message || '创建失败');
        showMessage('客户创建成功', 'success');
      }
      setModalOpen(false);
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '操作失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setActionLoading(true);
    try {
      const res = (await customerApi.delete(deleteTarget.id)) as unknown as { success: boolean; message?: string };
      if (!res.success) throw new Error(res.message || '删除失败');
      showMessage('客户删除成功', 'success');
      setDeleteTarget(null);
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '删除失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStatusChange = async (item: Customer, status: number) => {
    setActionLoading(true);
    try {
      const res = (await customerApi.updateStatus(item.id, status)) as unknown as {
        success: boolean;
        message?: string;
      };
      if (!res.success) throw new Error(res.message || '状态更新失败');
      showMessage('状态更新成功', 'success');
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '状态更新失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>客户列表</CardTitle>
          <Button size="sm" onClick={openCreate}>
            <Plus size={16} />
            新增客户
          </Button>
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

          <div className="flex flex-wrap gap-3 items-end">
            <Input
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder="客户名称"
              className="w-48"
            />
            <div className="w-40 space-y-1.5">
              <label className="text-sm font-medium text-foreground">状态</label>
              <Select value={customerStatus} options={STATUS_OPTIONS} onChange={(v) => { setCustomerStatus(v); setPage(1); }} />
            </div>
            <div className="w-48 space-y-1.5">
              <label className="text-sm font-medium text-foreground">代理</label>
              <Select value={agentId} options={agentFilterOptions} onChange={(v) => { setAgentId(v); setPage(1); }} searchable />
            </div>
            <Button onClick={handleSearch}>查询</Button>
          </div>

          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="data-table">
              <thead className="bg-background-tertiary">
                <tr>
                  <th>客户名称</th>
                  <th>客户编码</th>
                  <th>状态</th>
                  <th>代理</th>
                  <th>价差</th>
                  <th>合同开始</th>
                  <th>合同结束</th>
                  <th>联系人</th>
                  <th className="text-right">操作</th>
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
                    const statusMeta = STATUS_MAP[item.customer_status] || { label: '未知', color: 'bg-foreground/10 text-foreground' };
                    return (
                      <tr key={item.id} className="hover:bg-background-hover">
                        <td className="font-medium">{item.customer_name}</td>
                        <td>{item.customer_code || '-'}</td>
                        <td>
                          <span className={cn('px-2 py-0.5 rounded text-xs', statusMeta.color)}>{statusMeta.label}</span>
                        </td>
                        <td>{item.agent_name || '-'}</td>
                        <td className="text-right font-mono-num">{item.price_difference ?? '-'}</td>
                        <td>{item.contract_start_date || '-'}</td>
                        <td>{item.contract_end_date || '-'}</td>
                        <td>
                          {item.contact_person || '-'} {item.contact_phone || ''}
                        </td>
                        <td className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button variant="ghost" size="icon" onClick={() => openEdit(item)} title="编辑">
                              <Pencil size={16} />
                            </Button>
                            {item.customer_status !== 4 && item.customer_status !== 5 && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleStatusChange(item, 4)}
                                title="终止"
                              >
                                终止
                              </Button>
                            )}
                            <Button variant="ghost" size="icon" onClick={() => setDeleteTarget(item)} title="删除">
                              <Trash2 size={16} className="text-danger" />
                            </Button>
                          </div>
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
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? '编辑客户' : '新增客户'}
        description={editing ? `修改 ${editing.customer_name} 的信息` : '填写客户基本信息'}
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalOpen(false)} disabled={actionLoading}>
              取消
            </Button>
            <Button onClick={handleSubmit} isLoading={actionLoading}>
              {editing ? '保存修改' : '创建'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="客户名称"
            value={form.customer_name}
            onChange={(e) => setForm((f) => ({ ...f, customer_name: e.target.value }))}
            error={formErrors.customer_name}
            placeholder="请输入客户名称"
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="客户编码"
              value={form.customer_code}
              onChange={(e) => setForm((f) => ({ ...f, customer_code: e.target.value }))}
              placeholder="可选"
            />
            <Input
              label="电压等级"
              value={form.voltage_level}
              onChange={(e) => setForm((f) => ({ ...f, voltage_level: e.target.value }))}
              placeholder="如 10kV"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">状态</label>
              <Select value={form.customer_status} options={FORM_STATUS_OPTIONS} onChange={(v) => setForm((f) => ({ ...f, customer_status: v }))} />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">代理</label>
              <Select value={form.agent_id} options={agentFormOptions} onChange={(v) => setForm((f) => ({ ...f, agent_id: v }))} searchable />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="联系人"
              value={form.contact_person}
              onChange={(e) => setForm((f) => ({ ...f, contact_person: e.target.value }))}
              placeholder="联系人姓名"
            />
            <Input
              label="联系电话"
              value={form.contact_phone}
              onChange={(e) => setForm((f) => ({ ...f, contact_phone: e.target.value }))}
              placeholder="联系电话"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="价差"
              type="number"
              step="0.0001"
              value={form.price_difference}
              onChange={(e) => setForm((f) => ({ ...f, price_difference: e.target.value }))}
              placeholder="元/度"
            />
            <div />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <DatePicker
              label="合同开始"
              value={form.contract_start_date}
              onChange={(v) => setForm((f) => ({ ...f, contract_start_date: v }))}
            />
            <DatePicker
              label="合同结束"
              value={form.contract_end_date}
              onChange={(v) => setForm((f) => ({ ...f, contract_end_date: v }))}
            />
          </div>
        </div>
      </Modal>

      <Modal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="确认删除"
        description={deleteTarget ? `确定删除客户「${deleteTarget.customer_name}」？删除后不可恢复。` : ''}
        footer={
          <>
            <Button variant="ghost" onClick={() => setDeleteTarget(null)} disabled={actionLoading}>
              取消
            </Button>
            <Button variant="danger" onClick={handleDelete} isLoading={actionLoading}>
              删除
            </Button>
          </>
        }
      >
        <div />
      </Modal>
    </div>
  );
}
