export interface Campaign {
  id: number;
  tenant_id: string;
  name: string;
  created_at: string;
}

export interface Candidate {
  id: number;
  filename: string;
  parse_status: string;
  parse_method: string;
  parse_chars: number;
  quality_score: number;
  quality_reason: string;
  pipeline_status: "Applied" | "Shortlisted" | "Interviewing" | "Offered" | "Rejected";
  created_at: string;
}

export interface ScreeningResult {
  candidate_id: number;
  filename: string;
  score_total: number;
  score_embed: number;
  score_rules: number;
  pipeline_status: string;
  parse_status: string;
  parse_method: string;
  quality_score: number;
  quality_reason: string;
  error?: string;
  notes?: string;
  evidence?: string[];
  rules?: any;
}

export interface PolicyDocument {
  id: number;
  filename: string;
  ingest_status: string;
  ingest_method: string;
  category: string;
  visibility: string;
  version: string;
  status: string;
  error: string | null;
}

export interface Citation {
  source: string;
  chunk_id: number;
  score: number;
  snippet: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}
