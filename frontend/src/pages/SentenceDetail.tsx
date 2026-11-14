import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, formatDateTime } from '../api'
import { ErrorBox, Loading, SourceBadge } from '../components'
import { wordDiff } from '../diff'

export default function SentenceDetail() {
  const id = Number(useParams().id)
  const qc = useQueryClient()
  const navigate = useNavigate()
  const sentence = useQuery({ queryKey: ['sentence', id], queryFn: () => api.sentence(id), enabled: Number.isFinite(id) })
  const dismiss = useMutation({
    mutationFn: (value: boolean) => api.setDismissed(id, value),
    onSuccess: (updated) => {
      qc.setQueryData(['sentence', id], updated)
      // 列表與統計都會受 is_dismissed 影響
      void qc.invalidateQueries({ queryKey: ['sentences'] })
      void qc.invalidateQueries({ queryKey: ['stats'] })
    },
  })
  const remove = useMutation({
    mutationFn: () => api.deleteSentence(id),
    onSuccess: () => {
      qc.removeQueries({ queryKey: ['sentence', id] })
      void qc.invalidateQueries({ queryKey: ['sentences'] })
      void qc.invalidateQueries({ queryKey: ['stats'] })
      navigate('/sentences', { replace: true })
    },
  })

  if (!Number.isFinite(id)) return <ErrorBox error={new Error('無效的句子編號')} />
  if (sentence.isPending) return <Loading />
  if (sentence.error) return <ErrorBox error={sentence.error} />
  const s = sentence.data
  const diff = wordDiff(s.original_text, s.corrected_text)
  const changed = diff.some((t) => t.op !== 'same')

  return (
    <>
      <p>
        <Link to="/sentences">← 回列表</Link>
      </p>
      <div className="card-head">
        <h1>句子 #{s.id}</h1>
        <div className="meta">
          <SourceBadge source={s.source} />
          <span className="muted">{formatDateTime(s.created_at)}</span>
          {s.is_dismissed && <span className="chip chip-muted">已標記誤判</span>}
        </div>
      </div>

      <section className="compare">
        <div className="card">
          <h2>原句</h2>
          <p className="sentence">
            {diff.map((t, i) =>
              t.op === 'added' ? null : (
                <span key={i} className={t.op === 'removed' ? 'diff-removed' : undefined}>
                  {t.text}
                </span>
              ),
            )}
          </p>
        </div>
        <div className="card">
          <h2>修正</h2>
          <p className="sentence">
            {diff.map((t, i) =>
              t.op === 'removed' ? null : (
                <span key={i} className={t.op === 'added' ? 'diff-added' : undefined}>
                  {t.text}
                </span>
              ),
            )}
          </p>
          {!changed && <p className="muted">與原句相同，沒有需要修正的地方。</p>}
        </div>
      </section>

      <section className="card">
        <h2>說明</h2>
        <p>{s.explanation || <span className="muted">（無）</span>}</p>
      </section>

      <section className="card">
        <h2>錯誤清單（{s.errors.length}）</h2>
        {s.errors.length === 0 ? (
          <p className="muted">這句沒有錯誤。</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>類型</th>
                <th>錯誤片段</th>
                <th>建議</th>
              </tr>
            </thead>
            <tbody>
              {s.errors.map((e) => (
                <tr key={e.id}>
                  <td>
                    <Link className="chip" to={`/sentences?error_type=${encodeURIComponent(e.error_type.name)}`}>
                      {e.error_type.name}
                    </Link>
                  </td>
                  <td>
                    <code className="diff-removed">{e.error_snippet}</code>
                  </td>
                  <td>
                    <code className="diff-added">{e.suggestion}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h2>誤判回饋</h2>
        <p className="muted">標記為誤判後，這句不再列入統計與預設列表；可以隨時取消。</p>
        <button type="button" className={s.is_dismissed ? 'btn' : 'btn btn-danger'} disabled={dismiss.isPending} onClick={() => dismiss.mutate(!s.is_dismissed)}>
          {dismiss.isPending ? '儲存中…' : s.is_dismissed ? '取消誤判標記' : '標記為誤判'}
        </button>
        {dismiss.error && <ErrorBox error={dismiss.error} />}
      </section>

      <section className="card">
        <h2>刪除</h2>
        <p className="muted">永久刪除這句與它的錯誤紀錄，無法復原。只是想排除統計的話請改用上面的誤判標記。</p>
        <button
          type="button"
          className="btn btn-danger"
          disabled={remove.isPending}
          onClick={() => {
            if (window.confirm(`確定要永久刪除句子 #${s.id}？`)) remove.mutate()
          }}
        >
          {remove.isPending ? '刪除中…' : '刪除這句'}
        </button>
        {remove.error && <ErrorBox error={remove.error} />}
      </section>
    </>
  )
}
