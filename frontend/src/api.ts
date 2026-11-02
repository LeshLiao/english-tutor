/** 所有後端呼叫集中在這裡：統一前綴、X-API-Key、錯誤處理。 */

export interface ErrorType {
  id: number
  name: string
  description: string | null
  created_at: string
}

export interface SentenceError {
  id: number
  error_type: ErrorType
  error_snippet: string
  suggestion: string
}

export interface Sentence {
  id: number
  original_text: string
  corrected_text: string
  explanation: string
  source: 'hook' | 'skill'
  is_dismissed: boolean
  created_at: string
  errors: SentenceError[]
}

export interface ErrorStat {
  error_type_id: number
  error_type: string
  count: number
}

export interface TrendPoint {
  period: string
  sentence_count: number
  error_count: number
}

export interface SentenceQuery {
  error_type?: string
  q?: string
  from?: string
  to?: string
  limit?: number
  offset?: number
  include_dismissed?: boolean
}

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api'
const API_KEY = import.meta.env.VITE_API_KEY as string | undefined

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function toQuery(params: object): string {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params) as [string, unknown][]) {
    if (v !== undefined && v !== '') qs.set(k, String(v))
  }
  const s = qs.toString()
  return s ? `?${s}` : ''
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { ...(init.headers as Record<string, string>) }
  if (API_KEY) headers['X-API-Key'] = API_KEY
  if (init.body) headers['Content-Type'] = 'application/json'
  const res = await fetch(`${BASE}${path}`, { ...init, headers })
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      /* 非 JSON 回應就用 statusText */
    }
    throw new ApiError(res.status, `${res.status} ${detail}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  errorTypes: () => request<ErrorType[]>('/error-types'),
  sentences: (query: SentenceQuery = {}) => request<Sentence[]>(`/sentences${toQuery(query)}`),
  sentence: (id: number) => request<Sentence>(`/sentences/${id}`),
  setDismissed: (id: number, is_dismissed: boolean) =>
    request<Sentence>(`/sentences/${id}`, { method: 'PATCH', body: JSON.stringify({ is_dismissed }) }),
  errorStats: (query: { from?: string; to?: string } = {}) =>
    request<ErrorStat[]>(`/stats/errors${toQuery(query)}`),
  trend: (query: { interval?: 'day' | 'week'; from?: string; to?: string } = {}) =>
    request<TrendPoint[]>(`/stats/trend${toQuery(query)}`),
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('zh-TW', { hour12: false })
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('zh-TW')
}
