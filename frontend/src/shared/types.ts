// Shared API types for the elec-proxy system
// These will be expanded as each module is implemented

export interface PageResult<T> {
  items: T[];
  list: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface CommonResult<T> {
  code: number;
  data: T;
  msg: string;
}

// Common enums
export type CustomerStatus = 1 | 2 | 3 | 4 | 5;
export type AgentType = 'major' | 'minor';
export type PackageType = 'flat_rate' | 'time_of_use';
export type InquiryStatus = 'pending' | 'processing' | 'quoted' | 'cooperated' | 'rejected' | 'expired';
export type CommissionStatus = 'pending_approval' | 'approved' | 'rejected' | 'settled' | 'paid';
export type ProfitStatus = 'pending' | 'processed' | 'settled' | 'error';
