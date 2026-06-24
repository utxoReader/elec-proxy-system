import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { inquiryApi } from '@/shared/api';
import type { InquiryStatus } from '@/shared/types';

interface InquiryDetailData {
  id: number;
  customer_name: string;
  usage_month: string;
  estimated_monthly_consumption: string;
  inquiry_status: InquiryStatus;
  package_type: string;
  quoted_price_difference: string;
  recommended_package_type: string;
  quote_valid_until: string;
  estimated_monthly_fee: string;
  estimated_savings: string;
  savings_rate: string;
  remark: string;
  reject_reason: string;
  cooperation_start_date: string;
  cooperation_end_date: string;
  created_at: string;
}

const STATUS_MAP: Record<InquiryStatus, string> = {
  pending: '待处理',
  processing: '处理中',
  quoted: '已报价',
  cooperated: '已合作',
  rejected: '已拒绝',
  expired: '已过期',
};

export default function InquiryDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<InquiryDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [quoteForm, setQuoteForm] = useState({
    price_difference: '',
    recommended_package_type: '',
    quote_valid_until: '',
    estimated_monthly_fee: '',
    estimated_savings: '',
    savings_rate: '',
    remark: '',
  });
  const [cooperateForm, setCooperateForm] = useState({ cooperation_start_date: '', cooperation_end_date: '' });
  const [terminateDate, setTerminateDate] = useState('');
  const [rejectReason, setRejectReason] = useState('');

  const fetchDetail = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await inquiryApi.get(Number(id));
      const data = (res as unknown as { data: InquiryDetailData }).data;
      setDetail(data);
      setQuoteForm({
        price_difference: String(data.quoted_price_difference || ''),
        recommended_package_type: String(data.recommended_package_type || ''),
        quote_valid_until: String(data.quote_valid_until || ''),
        estimated_monthly_fee: String(data.estimated_monthly_fee || ''),
        estimated_savings: String(data.estimated_savings || ''),
        savings_rate: String(data.savings_rate || ''),
        remark: String(data.remark || ''),
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDetail(); }, [id]);

  const handleQuote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      await inquiryApi.quote(Number(id), {
        price_difference: Number(quoteForm.price_difference),
        recommended_package_type: quoteForm.recommended_package_type,
        quote_valid_until: quoteForm.quote_valid_until,
        estimated_monthly_fee: Number(quoteForm.estimated_monthly_fee),
        estimated_savings: Number(quoteForm.estimated_savings),
        savings_rate: Number(quoteForm.savings_rate),
        remark: quoteForm.remark,
      });
      fetchDetail();
    } catch (err) {
      alert(err instanceof Error ? err.message : '报价失败');
    }
  };

  const handleAccept = async () => {
    if (!id || !confirm('确认接受报价？')) return;
    try {
      await inquiryApi.accept(Number(id));
      fetchDetail();
    } catch (err) {
      alert(err instanceof Error ? err.message : '接受失败');
    }
  };

  const handleReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      await inquiryApi.reject(Number(id), rejectReason);
      fetchDetail();
    } catch (err) {
      alert(err instanceof Error ? err.message : '拒绝失败');
    }
  };

  const handleCooperate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      await inquiryApi.cooperate(Number(id), cooperateForm);
      fetchDetail();
    } catch (err) {
      alert(err instanceof Error ? err.message : '合作失败');
    }
  };

  const handleTerminate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      await inquiryApi.terminate(Number(id), terminateDate);
      fetchDetail();
    } catch (err) {
      alert(err instanceof Error ? err.message : '终止失败');
    }
  };

  if (loading) return <div className="p-6 text-foreground-muted">加载中...</div>;
  if (!detail) return <div className="p-6 text-foreground-muted">未找到询价</div>;

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-foreground">询价详情 #{detail.id}</h1>
        <button onClick={() => navigate('/inquiries')} className="px-4 py-1.5 rounded-md border border-border text-sm text-foreground-secondary hover:bg-background-secondary">返回</button>
      </div>

      <div className="grid grid-cols-2 gap-4 p-4 rounded-lg border border-border bg-background-secondary text-sm">
        <div><span className="text-foreground-secondary">客户：</span>{detail.customer_name}</div>
        <div><span className="text-foreground-secondary">月份：</span>{detail.usage_month}</div>
        <div><span className="text-foreground-secondary">套餐：</span>{detail.package_type || '-'}</div>
        <div><span className="text-foreground-secondary">状态：</span><span className="px-2 py-0.5 rounded text-xs bg-accent/10 text-accent">{STATUS_MAP[detail.inquiry_status]}</span></div>
        <div><span className="text-foreground-secondary">预估用电量：</span>{Number(detail.estimated_monthly_consumption || 0).toFixed(2)}</div>
        <div><span className="text-foreground-secondary">报价价差：</span>{detail.quoted_price_difference ?? '-'}</div>
        <div><span className="text-foreground-secondary">创建时间：</span>{detail.created_at || '-'}</div>
      </div>

      {(detail.inquiry_status === 'pending' || detail.inquiry_status === 'processing') && (
        <form onSubmit={handleQuote} className="p-4 rounded-lg border border-border bg-background-secondary space-y-3">
          <h2 className="text-sm font-semibold text-foreground">报价</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <input type="number" step="0.0001" placeholder="价差" value={quoteForm.price_difference} onChange={e => setQuoteForm({ ...quoteForm, price_difference: e.target.value })} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
            <input placeholder="推荐套餐" value={quoteForm.recommended_package_type} onChange={e => setQuoteForm({ ...quoteForm, recommended_package_type: e.target.value })} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
            <input type="date" placeholder="报价有效期" value={quoteForm.quote_valid_until} onChange={e => setQuoteForm({ ...quoteForm, quote_valid_until: e.target.value })} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
            <input type="number" step="0.01" placeholder="预估月费" value={quoteForm.estimated_monthly_fee} onChange={e => setQuoteForm({ ...quoteForm, estimated_monthly_fee: e.target.value })} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
            <input type="number" step="0.01" placeholder="预估节省" value={quoteForm.estimated_savings} onChange={e => setQuoteForm({ ...quoteForm, estimated_savings: e.target.value })} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
            <input type="number" step="0.0001" placeholder="节省率" value={quoteForm.savings_rate} onChange={e => setQuoteForm({ ...quoteForm, savings_rate: e.target.value })} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          </div>
          <textarea placeholder="备注" value={quoteForm.remark} onChange={e => setQuoteForm({ ...quoteForm, remark: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" rows={2} />
          <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">提交报价</button>
        </form>
      )}

      {detail.inquiry_status === 'quoted' && (
        <div className="p-4 rounded-lg border border-border bg-background-secondary space-y-3">
          <h2 className="text-sm font-semibold text-foreground">接受报价</h2>
          <button onClick={handleAccept} className="px-4 py-1.5 rounded-md bg-success text-white text-sm hover:opacity-90">接受</button>
        </div>
      )}

      {(detail.inquiry_status === 'pending' || detail.inquiry_status === 'quoted') && (
        <form onSubmit={handleReject} className="p-4 rounded-lg border border-border bg-background-secondary space-y-3">
          <h2 className="text-sm font-semibold text-foreground">拒绝</h2>
          <input placeholder="拒绝原因" value={rejectReason} onChange={e => setRejectReason(e.target.value)} className="w-full px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          <button type="submit" className="px-4 py-1.5 rounded-md bg-danger text-white text-sm hover:opacity-90">拒绝</button>
        </form>
      )}

      {detail.inquiry_status === 'quoted' && (
        <form onSubmit={handleCooperate} className="p-4 rounded-lg border border-border bg-background-secondary space-y-3">
          <h2 className="text-sm font-semibold text-foreground">合作</h2>
          <div className="flex gap-3">
            <input type="date" placeholder="合作开始" value={cooperateForm.cooperation_start_date} onChange={e => setCooperateForm({ ...cooperateForm, cooperation_start_date: e.target.value })} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
            <input type="date" placeholder="合作结束" value={cooperateForm.cooperation_end_date} onChange={e => setCooperateForm({ ...cooperateForm, cooperation_end_date: e.target.value })} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          </div>
          <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">确认合作</button>
        </form>
      )}

      {detail.inquiry_status === 'cooperated' && (
        <form onSubmit={handleTerminate} className="p-4 rounded-lg border border-border bg-background-secondary space-y-3">
          <h2 className="text-sm font-semibold text-foreground">终止合作</h2>
          <input type="date" value={terminateDate} onChange={e => setTerminateDate(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          <button type="submit" className="px-4 py-1.5 rounded-md bg-danger text-white text-sm hover:opacity-90">终止</button>
        </form>
      )}
    </div>
  );
}
