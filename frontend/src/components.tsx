import type { ReactNode } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api, ApiError, formatDateTime, type Sentence } from './api'

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

/**
 * 句子列表（總覽與列表頁共用）。
 * 桌機是一般表格；手機（index.css 的 640px 斷點）每列變成卡片：
 *   時間 | 來源 | 刪除鈕
 *   錯誤類型
 *   原句
 */
export function SentenceTable({ sentences, showId = false }: { sentences: Sentence[]; showId?: boolean }) {
  const qc = useQueryClient()
  const remove = useMutation({
    mutationFn: (id: number) => api.deleteSentence(id),
    onSuccess: (_, id) => {
      qc.removeQueries({ queryKey: ['sentence', id] })
      void qc.invalidateQueries({ queryKey: ['sentences'] })
      void qc.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  return (
    <>
      {remove.error && <ErrorBox error={remove.error} />}
      <table className="table sentence-table">
        <thead>
          <tr>
            {showId && <th>#</th>}
            <th>時間</th>
            <th>原句</th>
            <th>錯誤類型</th>
            <th>來源</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {sentences.map((s) => {
            const deleting = remove.isPending && remove.variables === s.id
            return (
              <tr key={s.id} className={s.is_dismissed ? 'dismissed' : undefined}>
                {showId && <td className="muted col-id">{s.id}</td>}
                <td className="nowrap muted col-time">{formatDateTime(s.created_at)}</td>
                <td className="col-text">
                  <Link to={`/sentences/${s.id}`}>{s.original_text}</Link>
                  {s.is_dismissed && <span className="chip chip-muted">誤判</span>}
                </td>
                <td className="col-types">
                  <ErrorTypeChips sentence={s} />
                </td>
                <td className="col-source">
                  <SourceBadge source={s.source} />
                </td>
                <td className="col-actions">
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm btn-delete"
                    disabled={deleting}
                    onClick={() => {
                      if (window.confirm(`確定要永久刪除句子 #${s.id}？`)) remove.mutate(s.id)
                    }}
                  >
                    {deleting ? '刪除中…' : '刪除'}
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </>
  )
}
