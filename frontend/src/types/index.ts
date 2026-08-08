export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  company: Company | null;
  created_at: string;
}

export interface Company {
  id: number;
  name: string;
  commercial_register: string | null;
  tax_number: string | null;
  logo_url: string | null;
  subscription_plan: 'FREE' | 'PRO' | 'ENTERPRISE';
  subscription_end_date: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
  company_name: string;
  commercial_register?: string;
  tax_number?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
}

export type AnalysisStatus =
  | 'queued'
  | 'processing'
  | 'completed'
  | 'partially_completed'
  | 'failed'
  | 'needs_review';

export interface RFPUploadResponse {
  analysis_id: number;
  task_id: string;
  status: AnalysisStatus;
  message: string;
  check_status_url: string;
}

export interface RFPStatusResponse {
  id: number;
  status: AnalysisStatus;
  quality_score: string | null;
  confidence_score: number;
  progress: number;
  retry_count: number;
  attempt: number;
  completed_at: string | null;
  error_message: string | null;
  result: any | null;
}

export interface RFPAnalysisItem {
  id: number;
  filename: string;
  status: AnalysisStatus;
  quality_score: string | null;
  confidence_score: number;
  created_at: string;
  completed_at: string | null;
}