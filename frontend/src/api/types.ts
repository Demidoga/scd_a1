// Mirrors backend/app/domain/schemas.py and backend/app/domain/enums.py.
// This is the frontend half of the typed API boundary described in
// docs/architecture/frontend.md §4 — the backend's Pydantic models/OpenAPI
// schema are the source of truth; these types must track them, not diverge.

export const CATEGORIES = [
  'water',
  'electricity',
  'sanitation',
  'roads',
  'streetlights',
  'other',
] as const
export type Category = (typeof CATEGORIES)[number]

export const PRIORITIES = ['high', 'normal', 'low'] as const
export type Priority = (typeof PRIORITIES)[number]

export const STATUSES = ['open', 'in_progress', 'resolved', 'rejected'] as const
export type Status = (typeof STATUSES)[number]

export interface ComplaintCreate {
  text: string
  location: string
  reporter_contact?: string | null
}

export interface ComplaintStatusUpdate {
  status: Status
}

export interface ComplaintResponse {
  id: string
  text: string
  location: string
  reporter_contact: string | null
  category: Category
  priority: Priority
  status: Status
  allowed_transitions: Status[]
  ai_summary: string | null
  triaged_by: string
  triage_latency_ms: number
  created_at: string
  updated_at: string
}

export interface ComplaintListResponse {
  items: ComplaintResponse[]
  total: number
  page: number
  page_size: number
}

export interface FieldError {
  field: string
  message: string
}

export interface ErrorResponse {
  detail: string
  errors?: FieldError[] | null
}

export interface StatsResponse {
  total: number
  by_status: Record<string, number>
  by_category: Record<string, number>
  by_priority: Record<string, number>
}

export interface TriageOutcome {
  complaint_id: string
  provider: string
  latency_ms: number
  fallback_used: boolean
  created_at: string
}

export interface ProvidersMetaResponse {
  active_provider: string
  recent_outcomes: TriageOutcome[]
}

export interface ComplaintFilters {
  category?: Category
  priority?: Priority
  status?: Status
  page?: number
  page_size?: number
}
