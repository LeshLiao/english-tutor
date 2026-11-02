import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, type Sentence } from './api'

export function Loading() {
  return <p className="muted">載入中…</p>
}

export function ErrorBox({ error }: { error: unknown }) {
  const msg =
    error instanceof ApiError
      ? error.status === 401
        ? '後端拒絕 API key，請確認 frontend/.env.development 的 VITE_API_KEY 與根目錄 .env 的 API_KEY 相同。'
        : error.message
      : error instanceof Error
        ? `${error.message}。後端可能沒有啟動（docker compose up -d）。`
        : String(error)
  return (
    <p className="error-box" role="alert">
      {msg}
    </p>
  )
}

export function Empty({ children = '沒有資料' }: { children?: ReactNode }) {
  return <p className="muted">{children}</p>
}

export function ErrorTypeChips({ sentence }: { sentence: Sentence }) {
  const names = [...new Set(sentence.errors.map((e) => e.error_type.name))]
  if (names.length === 0) return <span className="chip chip-ok">正確</span>
  return (
    <>
      {names.map((n) => (
        <Link key={n} className="chip" to={`/sentences?error_type=${encodeURIComponent(n)}`}>
          {n}
        </Link>
      ))}
    </>
  )
}

export function SourceBadge({ source }: { source: Sentence['source'] }) {
  return <span className={`badge badge-${source}`}>{source}</span>
}
