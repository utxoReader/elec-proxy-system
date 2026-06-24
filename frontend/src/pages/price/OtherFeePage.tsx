import { priceApi } from '@/shared/api';
import PriceTable from './PriceTable';

export default function OtherFeePage() {
  return (
    <PriceTable
      title="其他费用"
      fetchFn={priceApi.otherFeePage}
      columns={[
        { key: 'month_config', label: '月份' },
        { key: 'distribution_price', label: '输配电价(元/度)', align: 'right' },
        { key: 'government_fund', label: '政府性基金(元/度)', align: 'right' },
        { key: 'cross_subsidy', label: '交叉补贴(元/度)', align: 'right' },
        { key: 'line_loss_fee', label: '线损费(元/度)', align: 'right' },
        { key: 'status', label: '状态' },
        { key: 'remark', label: '备注' },
      ]}
    />
  );
}
