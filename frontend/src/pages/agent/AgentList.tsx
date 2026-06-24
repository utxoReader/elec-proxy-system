import { useEffect, useMemo, useState } from 'react';
import { agentApi } from '@/shared/api';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { Modal } from '@/shared/ui/Modal';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/Card';
import { cn } from '@/shared/utils';
import { Plus, Pencil, Trash2, RotateCcw, AlertCircle } from 'lucide-react';

interface Agent {
  id: number;
  name: string;
  type: number;
  parent_id: number | null;
  status: number;
  tax_type: number | null;
  remark: string | null;
  created_at?: string;
}

type AgentFormData = {
  name: string;
  type: string;
  parent_id: string;
  status: string;
  tax_type: string;
  remark: string;
};

const TYPE_MAP: Record<number, string> = { 1: '大代理', 2: '小代理' };
const TYPE_OPTIONS = [
  { value: '1', label: '大代理' },
  { value: '2', label: '小代理' },
];
const TAX_OPTIONS = [
  { value: '', label: '请选择' },
  { value: '1', label: '专票13%' },
  { value: '2', label: '专票6%' },
  { value: '3', label: '普票' },
  { value: '4', label: '没票' },
];
const STATUS_OPTIONS = [
  { value: '0', label: '启用' },
  { value: '1', label: '禁用' },
];

const emptyForm: AgentFormData = {
  name: '',
  type: '1',
  parent_id: '',
  status: '0',
  tax_type: '',
  remark: '',
};

function agentToForm(agent: Agent): AgentFormData {
  return {
    name: agent.name,
    type: String(agent.type || 1),
    parent_id: agent.parent_id ? String(agent.parent_id) : '',
    status: String(agent.status ?? 0),
    tax_type: agent.tax_type ? String(agent.tax_type) : '',
    remark: agent.remark || '',
  };
}

function formToCreate(data: AgentFormData): Record<string, unknown> {
  return {
    name: data.name.trim(),
    type: Number(data.type),
    parent_id: data.parent_id ? Number(data.parent_id) : null,
    status: Number(data.status),
    tax_type: data.tax_type ? Number(data.tax_type) : null,
    remark: data.remark.trim() || null,
  };
}

export default function AgentList() {
  const [data, setData] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Agent | null>(null);
  const [form, setForm] = useState<AgentFormData>(emptyForm);
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof AgentFormData, string>>>({});

  const [deleteTarget, setDeleteTarget] = useState<Agent | null>(null);

  const parentOptions = useMemo(
    () => [{ value: '', label: '无上级代理' }, ...data
      .filter((a) => !editing || a.id !== editing.id)
      .map((a) => ({ value: String(a.id), label: a.name }))],
    [data, editing]
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

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = (await agentApi.list()) as unknown as { success: boolean; data?: Agent[]; message?: string };
      if (res.success) {
        setData(res.data || []);
      } else {
        showMessage(res.message || '加载代理商失败', 'error');
      }
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '加载代理商失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setFormErrors({});
    setModalOpen(true);
  };

  const openEdit = (agent: Agent) => {
    setEditing(agent);
    setForm(agentToForm(agent));
    setFormErrors({});
    setModalOpen(true);
  };

  const validate = (): boolean => {
    const errors: Partial<Record<keyof AgentFormData, string>> = {};
    if (!form.name.trim()) errors.name = '代理商名称不能为空';
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    setActionLoading(true);
    try {
      const payload = formToCreate(form);
      if (editing) {
        const res = (await agentApi.update({ id: editing.id, ...payload })) as unknown as {
          success: boolean;
          message?: string;
        };
        if (!res.success) throw new Error(res.message || '更新失败');
        showMessage('代理商更新成功', 'success');
      } else {
        const res = (await agentApi.create(payload)) as unknown as {
          success: boolean;
          message?: string;
        };
        if (!res.success) throw new Error(res.message || '创建失败');
        showMessage('代理商创建成功', 'success');
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
      const res = (await agentApi.delete(deleteTarget.id)) as unknown as {
        success: boolean;
        message?: string;
      };
      if (!res.success) throw new Error(res.message || '删除失败');
      showMessage('代理商删除成功', 'success');
      setDeleteTarget(null);
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '删除失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleStatus = async (agent: Agent) => {
    const nextStatus = agent.status === 0 ? 1 : 0;
    setActionLoading(true);
    try {
      const res = (await agentApi.updateStatus(agent.id, nextStatus)) as unknown as {
        success: boolean;
        message?: string;
      };
      if (!res.success) throw new Error(res.message || '状态更新失败');
      showMessage(`已${nextStatus === 0 ? '启用' : '禁用'}该代理商`, 'success');
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
          <CardTitle>代理商管理</CardTitle>
          <Button size="sm" onClick={openCreate}>
            <Plus size={16} />
            新增代理商
          </Button>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">
              <AlertCircle size={16} />
              {error}
            </div>
          )}
          {success && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-success/20 bg-success/10 px-4 py-3 text-sm text-success">
              <RotateCcw size={16} />
              {success}
            </div>
          )}
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="data-table">
              <thead className="bg-background-tertiary">
                <tr>
                  <th>ID</th>
                  <th>名称</th>
                  <th>类型</th>
                  <th>上级代理</th>
                  <th>税率类型</th>
                  <th>状态</th>
                  <th className="text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-foreground-muted">
                      加载中...
                    </td>
                  </tr>
                ) : data.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-foreground-muted">
                      暂无数据
                    </td>
                  </tr>
                ) : (
                  data.map((item) => (
                    <tr key={item.id} className="hover:bg-background-hover">
                      <td>{item.id}</td>
                      <td className="font-medium">{item.name}</td>
                      <td>{TYPE_MAP[item.type] || '未知'}</td>
                      <td className="text-foreground-secondary">
                        {data.find((p) => p.id === item.parent_id)?.name || '-'}
                      </td>
                      <td className="text-sm">
                        {TAX_OPTIONS.find((o) => o.value === String(item.tax_type))?.label || '-'}
                      </td>
                      <td>
                        <button
                          onClick={() => handleToggleStatus(item)}
                          disabled={actionLoading}
                          className={cn(
                            'px-2 py-0.5 rounded text-xs transition-colors',
                            item.status === 0
                              ? 'bg-success/10 text-success hover:bg-success/20'
                              : 'bg-danger/10 text-danger hover:bg-danger/20'
                          )}
                        >
                          {item.status === 0 ? '启用' : '禁用'}
                        </button>
                      </td>
                      <td className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="ghost" size="icon" onClick={() => openEdit(item)} title="编辑">
                            <Pencil size={16} />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => setDeleteTarget(item)} title="删除">
                            <Trash2 size={16} className="text-danger" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Create / Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? '编辑代理商' : '新增代理商'}
        description={editing ? `修改 ${editing.name} 的信息` : '填写代理商基本信息'}
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
            label="代理商名称"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            error={formErrors.name}
            placeholder="请输入代理商名称"
          />
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">代理类型</label>
              <Select
                value={form.type}
                options={TYPE_OPTIONS}
                onChange={(v) => setForm((f) => ({ ...f, type: v }))}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">上级代理</label>
              <Select
                value={form.parent_id}
                options={parentOptions}
                onChange={(v) => setForm((f) => ({ ...f, parent_id: v }))}
                searchable
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">税率类型</label>
              <Select
                value={form.tax_type}
                options={TAX_OPTIONS}
                onChange={(v) => setForm((f) => ({ ...f, tax_type: v }))}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">状态</label>
              <Select
                value={form.status}
                options={STATUS_OPTIONS}
                onChange={(v) => setForm((f) => ({ ...f, status: v }))}
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">备注</label>
            <textarea
              value={form.remark}
              onChange={(e) => setForm((f) => ({ ...f, remark: e.target.value }))}
              rows={3}
              className={cn(
                'flex w-full rounded-lg border px-3 py-2 text-sm',
                'bg-background-tertiary text-foreground',
                'border-transparent placeholder:text-foreground-tertiary',
                'transition-all duration-200',
                'focus:outline-none focus:border-foreground'
              )}
              placeholder="可选备注"
            />
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <Modal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="确认删除"
        description={deleteTarget ? `确定删除代理商「${deleteTarget.name}」？删除后不可恢复。` : ''}
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
