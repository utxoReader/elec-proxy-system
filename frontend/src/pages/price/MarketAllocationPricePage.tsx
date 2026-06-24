import { priceApi } from '@/shared/api';
import PriceTable from './PriceTable';

export default function MarketAllocationPricePage() {
  return (
    <PriceTable
      title="市场分摊价"
      fetchFn={priceApi.marketAllocationPage}
      columns={[
        { key: 'year_month', label: '年月' },
        { key: 'price_date', label: '价格日期' },
        { key: 'allocation_price', label: '分摊价(元/度)', align: 'right' },
        { key: 'status', label: '状态' },
        { key: 'remark', label: '备注' },
      ]}
    />
  );
}
