import { priceApi } from '@/shared/api';
import PriceTable from './PriceTable';

export default function BasePricePage() {
  return (
    <PriceTable
      title="基础分时电价"
      fetchFn={priceApi.basePricePage}
      columns={[
        { key: 'price_type', label: '价格类型' },
        { key: 'price_date', label: '价格日期' },
        { key: 'hour_index', label: '时段', align: 'right' },
        { key: 'price', label: '价格(元/度)', align: 'right' },
        { key: 'status', label: '状态' },
      ]}
    />
  );
}
