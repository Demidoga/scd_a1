// Typed API client — the frontend's only path to the backend
// (docs/architecture/frontend.md §4). Always calls same-origin `/api/...`
// paths; never an absolute backend URL, so no environment-specific hostname
// is ever baked into the built bundle (nginx / vite proxy handles routing).

import type {
  ComplaintCreate,
  ComplaintFilters,
  ComplaintListResponse,
  ComplaintResponse,
  ComplaintStatusUpdate,
  ErrorResponse,
  ProvidersMetaResponse,
  StatsResponse,
} from './types'

export class ApiError extends Error {
  readonly status: number
  readonly body: ErrorResponse | null

  constructor(status: number, body: ErrorResponse | null) {
    super(body?.detail ?? `Request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...init?.headers,
      },
    })
  } catch {
    throw new ApiError(0, { detail: 'Network error: could not reach the server' })
  }

  if (!response.ok) {
    let body: ErrorResponse | null = null
    try {
      body = (await response.json()) as ErrorResponse
    } catch {
      // non-JSON error body; fall through with body left null
    }
    throw new ApiError(response.status, body)
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export interface StatsResult {
  stats: StatsResponse
  cacheStatus: 'HIT' | 'MISS' | 'UNKNOWN'
}

export const api = {
  createComplaint(payload: ComplaintCreate): Promise<ComplaintResponse> {
    return request('/api/complaints', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  getComplaint(id: string): Promise<ComplaintResponse> {
    return request(`/api/complaints/${id}`)
  },

  listComplaints(filters: ComplaintFilters): Promise<ComplaintListResponse> {
    const params = new URLSearchParams()
    if (filters.category) params.set('category', filters.category)
    if (filters.priority) params.set('priority', filters.priority)
    if (filters.status) params.set('status', filters.status)
    params.set('page', String(filters.page ?? 1))
    params.set('page_size', String(filters.page_size ?? 20))
    return request(`/api/complaints?${params.toString()}`)
  },

  updateComplaintStatus(
    id: string,
    payload: ComplaintStatusUpdate,
  ): Promise<ComplaintResponse> {
    return request(`/api/complaints/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  async getStats(): Promise<StatsResult> {
    const response = await fetch('/api/stats')
    if (!response.ok) {
      let body: ErrorResponse | null = null
      try {
        body = (await response.json()) as ErrorResponse
      } catch {
        // ignore
      }
      throw new ApiError(response.status, body)
    }
    const cacheHeader = response.headers.get('X-Cache')
    const cacheStatus = cacheHeader === 'HIT' || cacheHeader === 'MISS' ? cacheHeader : 'UNKNOWN'
    const stats = (await response.json()) as StatsResponse
    return { stats, cacheStatus }
  },

  getProvidersMeta(): Promise<ProvidersMetaResponse> {
    return request('/api/meta/providers')
  },
}
