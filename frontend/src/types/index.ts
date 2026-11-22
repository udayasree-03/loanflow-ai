export type ApplicationStatus =
  | 'draft'
  | 'submitted'
  | 'processing'
  | 'underwritten'
  | 'approved'
  | 'rejected';

export type DocumentType =
  | 'w2'
  | 'paystub'
  | 'form_1040'
  | 'bank_statement'
  | 'unclassified';

export type UnderwritingDecisionStatus =
  | 'APPROVED'
  | 'REFER_TO_HUMAN'
  | 'REJECTED';

export type DiscrepancySeverity = 'low' | 'medium' | 'high' | 'critical';

export interface MortgageDocumentSummary {
  id: string;
  document_type: DocumentType;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  status: string;
  created_at: string;
}

export interface LoanApplication {
  id: string;
  borrower_name: string;
  borrower_email: string;
  borrower_phone: string | null;
  loan_amount: number;
  property_address: string | null;
  status: ApplicationStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
  documents: MortgageDocumentSummary[];
}

export interface ExtractionResult {
  id: string;
  document_id: string;
  raw_text: string;
  structured_data: Record<string, any>;
  confidence_score: number | null;
  page_count: number;
  extraction_method: string;
  status: string;
  error_message: string | null;
}

export interface DocumentDetail {
  id: string;
  loan_application_id: string | null;
  document_type: DocumentType;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  status: string;
  created_at: string;
  extraction_result: ExtractionResult | null;
}

export interface DiscrepancyFlag {
  severity: DiscrepancySeverity;
  category: string;
  field: string;
  message: string;
  document_a?: string | null;
  value_a?: string | null;
  document_b?: string | null;
  value_b?: string | null;
  variance_pct?: number | null;
}

export interface DTIAnalysis {
  loan_amount: number;
  property_value: number;
  ltv_ratio_pct: number;
  qualifying_monthly_income: number;
  estimated_monthly_pi: number;
  estimated_monthly_escrow: number;
  total_monthly_housing_expense: number;
  monthly_non_housing_debt: number;
  total_monthly_debt: number;
  front_end_dti_pct: number;
  back_end_dti_pct: number;
  max_allowed_dti_pct: number;
  passes_front_end: boolean;
  passes_back_end: boolean;
}

export interface UnderwritingDecision {
  status: UnderwritingDecisionStatus;
  confidence_score: number;
  summary: string;
  key_findings: string[];
  conditions: string[];
}

export interface ExtractedFinancialEntities {
  borrower_name: string | null;
  employer_name: string | null;
  w2_annual_wages: number | null;
  w2_federal_tax: number | null;
  paystub_gross_pay: number | null;
  paystub_pay_frequency: string | null;
  paystub_annualized_income: number | null;
  form_1040_tax_year: number | null;
  form_1040_total_wages: number | null;
  form_1040_adjusted_gross_income: number | null;
  bank_statement_ending_balance: number | null;
  qualifying_monthly_income: number;
  income_source_documents: string[];
}

export interface UnderwritingResult {
  application_id: string;
  borrower_name: string;
  loan_amount: number;
  status: UnderwritingDecisionStatus;
  decision: UnderwritingDecision;
  dti_analysis: DTIAnalysis;
  financial_entities: ExtractedFinancialEntities;
  flags: DiscrepancyFlag[];
  reasoning_log: string[];
  document_count: number;
  created_at: string;
}

export interface CreateApplicationPayload {
  borrower_name: string;
  borrower_email: string;
  borrower_phone?: string;
  loan_amount: number;
  property_address?: string;
}

export interface UnderwritePayload {
  property_value?: number;
  monthly_debt?: number;
  interest_rate_pct?: number;
  loan_term_years?: number;
}
