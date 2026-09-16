export interface Customer {
  id: number;
  customer_id_str?: string;
  customer_name: string;
  contact_number?: string;
  normalized_contact?: string;
  full_address?: string;
  pincode?: string;
  post_office?: string;
  district?: string;
  state?: string;
  first_order_date?: string;
  last_order_date?: string;
  total_orders: number;
  total_spend: number;
  average_order_value: number;
  rfm_score?: string;
  rfm_segment?: string;
  created_at: string;
  updated_at: string;
}

export interface CustomerRFMInfo {
  recency_days: number;
  frequency: number;
  monetary_value: number;
  r_score: number;
  f_score: number;
  m_score: number;
  rfm_score: string;
  segment: string;
}

export interface CustomerProductSummary {
  product_name: string;
  sku?: string;
  category?: string;
  total_quantity: number;
  total_spend: number;
  last_purchased_date?: string;
}

export interface CustomerDetail extends Customer {
  rfm_details?: CustomerRFMInfo;
  formatted_clipboard_text?: string;
  purchased_products?: CustomerProductSummary[];
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id?: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  discount: number;
  item_total: number;
}

export interface Order {
  id: number;
  order_number: string;
  customer_id: number;
  customer_name?: string;
  customer_contact?: string;
  customer_district?: string;
  customer_pincode?: string;
  order_date: string;
  employee_id?: number;
  employee_name?: string;
  payment_mode: 'COD' | 'PREPAID' | string;
  order_status: 'DELIVERED' | 'COMPLETED' | 'CANCELLED' | 'RETURNED' | 'REFUNDED' | 'PENDING' | string;
  subtotal: number;
  discount: number;
  shipping_charge: number;
  tax: number;
  total_amount: number;
  revenue_amount: number;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

export interface Product {
  id: number;
  product_name: string;
  sku?: string;
  category?: string;
  price: number;
  total_units_sold: number;
  total_orders: number;
  total_revenue: number;
  avg_revenue_per_order: number;
  revenue_contribution_pct: number;
  created_at: string;
  updated_at: string;
}

export interface Employee {
  id: number;
  employee_name: string;
  employee_code?: string;
  status: 'ACTIVE' | 'INACTIVE' | string;
  total_orders: number;
  total_revenue: number;
  average_order_value: number;
  customer_count: number;
  cod_revenue: number;
  prepaid_revenue: number;
  created_at: string;
  updated_at: string;
}

export interface PostalOffice {
  id: number;
  pincode: string;
  office_name: string;
  office_type?: string;
  delivery_status?: string;
  district?: string;
  state?: string;
}

export interface PostalMaster {
  pincode: string;
  district?: string;
  state?: string;
  region?: string;
  division?: string;
  circle?: string;
  country: string;
  offices: PostalOffice[];
  created_at?: string;
  updated_at?: string;
}

export interface DateWiseMetric {
  date: string;
  revenue: number;
  orders: number;
  aov: number;
}

export interface PaymentModeBreakdown {
  payment_mode: string;
  revenue: number;
  order_count: number;
  average_order_value?: number;
  percentage_revenue: number;
  percentage_orders: number;
}

export interface BusinessDashboardKPIs {
  total_revenue: number;
  total_orders: number;
  average_order_value: number;
  total_customers: number;
  total_products: number;
  cod_revenue: number;
  prepaid_revenue: number;
  cod_orders: number;
  prepaid_orders: number;
  cod_aov?: number;
  prepaid_aov?: number;
  revenue_trend: DateWiseMetric[];
  payment_breakdown: PaymentModeBreakdown[];
}

export interface DistrictAnalyticsItem {
  district: string;
  state?: string;
  customer_count: number;
  total_orders: number;
  total_revenue: number;
}

export interface PincodeAnalyticsItem {
  pincode: string;
  district: string;
  state?: string;
  customer_count: number;
  total_orders: number;
  total_revenue: number;
}

export interface RFMSegmentSummary {
  segment_name: string;
  customer_count: number;
  percentage: number;
  total_revenue: number;
  avg_monetary: number;
  avg_frequency: number;
  avg_recency_days: number;
  color_code: string;
}

export interface ScoreDistribution {
  score: number;
  customer_count: number;
}

export interface RFMDashboardData {
  total_customers_with_rfm: number;
  customers_without_sufficient_data: number;
  avg_recency_days: number;
  avg_frequency: number;
  avg_monetary: number;
  segments: RFMSegmentSummary[];
  recency_distribution: ScoreDistribution[];
  frequency_distribution: ScoreDistribution[];
  monetary_distribution: ScoreDistribution[];
}

export interface UploadRowItem {
  id: number;
  row_number: number;
  status: string;
  raw_data?: string;
  error_reason?: string;
  suggested_fix?: string;
}

export interface UploadBatch {
  id: number;
  file_name: string;
  upload_type: string;
  uploaded_date: string;
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  duplicate_rows: number;
  updated_rows: number;
  new_customers: number;
  new_orders: number;
  new_products: number;
  status: 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'PARTIALLY_COMPLETED' | 'FAILED';
  error_message?: string;
  failed_row_items?: UploadRowItem[];
}

export interface FileAnalysisResponse {
  file_name: string;
  temp_file_id: string;
  total_rows: number;
  detected_columns: string[];
  suggested_import_type: 'CUSTOMER' | 'ORDER' | 'PRODUCT' | 'COMBINED';
  auto_mappings: Record<string, string | null>;
  sample_rows: Record<string, any>[];
  validation_warnings: string[];
}

export interface DataQualityIssue {
  id: number;
  entity_type: string;
  entity_id?: string;
  row_number?: number;
  batch_id?: number;
  field_name: string;
  issue_type: string;
  raw_value?: string;
  message: string;
  suggested_fix?: string;
  is_resolved: boolean;
  created_at: string;
}

export interface DataQualitySummary {
  total_issues: number;
  unresolved_issues: number;
  resolved_issues: number;
  by_type: Record<string, number>;
  by_entity: Record<string, number>;
}

export interface SystemSettings {
  revenue_rules: {
    delivered_eligible: boolean;
    completed_eligible: boolean;
    cancelled_eligible: boolean;
    returned_eligible: boolean;
    refunded_eligible: boolean;
    pending_eligible: boolean;
  };
  rfm_settings: {
    recency_weight: number;
    frequency_weight: number;
    monetary_weight: number;
  };
  postal_api_url: string;
  database_url_masked: string;
  app_version: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GlobalFilterState {
  preset: string;
  startDate?: string;
  endDate?: string;
  employeeId?: number;
  productId?: number;
  paymentMode?: string;
  district?: string;
  pincode?: string;
  rfmSegment?: string;
  orderStatus?: string;
  search?: string;
  customerId?: number;
}

export interface UnknownLocationSummary {
  unknown_pincode_count: number;
  unknown_district_count: number;
  both_unknown_count: number;
  total_unresolved: number;
}

export interface UnknownLocationRecord {
  id: number;
  customer_id_str?: string;
  customer_name: string;
  contact_number?: string;
  normalized_contact?: string;
  full_address?: string;
  pincode?: string;
  post_office?: string;
  district?: string;
  state?: string;
  total_orders: number;
  total_spend: number;
  missing_type: 'UNKNOWN_PINCODE' | 'UNKNOWN_DISTRICT' | 'BOTH_UNKNOWN';
  created_at: string;
}

export interface LocationCorrectionRequest {
  pincode?: string;
  post_office?: string;
  district?: string;
  state?: string;
  notes?: string;
  source?: 'MANUAL' | 'POSTAL_API' | 'BULK_UPDATE';
}

export interface BulkLocationCorrectionRequest {
  customer_ids: number[];
  pincode?: string;
  post_office?: string;
  district?: string;
  state?: string;
  notes?: string;
  source?: 'BULK_UPDATE' | 'POSTAL_API';
}

export interface LocationAuditLog {
  id: number;
  customer_id: number;
  customer_name?: string;
  previous_pincode?: string;
  new_pincode?: string;
  previous_district?: string;
  new_district?: string;
  previous_post_office?: string;
  new_post_office?: string;
  previous_state?: string;
  new_state?: string;
  correction_source: string;
  changed_by: string;
  notes?: string;
  created_at: string;
}

