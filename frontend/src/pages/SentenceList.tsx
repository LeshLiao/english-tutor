import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { api, formatDateTime } from '../api'
import { Empty, ErrorBox, ErrorTypeChips, Loading, SourceBadge } from '../components'

const PAGE_SIZE = 20

export default function SentenceList() {
  const [params, setParams] = useSearchParams()
  const errorType = params.get('error_type') ?? ''
  const q = params.get('q') ?? ''
  const from = params.get('from') ?? ''
  const to = params.get('to') ?? ''
  const includeDismissed = params.get('include_dismissed') === '1'
  const page = Math.max(1, Number(params.get('page') ?? '1'))

  const query = {
    error_type: errorType || undefined,
    q: q || undefined,
    // 日期欄位是本地日期；to 取當天結束，才會包含當天的句子
    from: from ? new Date(`${from}T00:00:00`).toISOString() : undefined,
    to: to ? new Date(`${to}T23:59:59.999`).toISOString() : undefined,
    include_dismissed: includeDismissed || undefined,
    limit: PAGE_SIZE,
    offset: (page - 1) * PAGE_SIZE,
  }

  const types = useQuery({ queryKey: ['error-types'], queryFn: api.errorTypes })
  const list = useQuery({ queryKey: ['sentences', query], queryFn: () => api.sentences(query) })

  function update(changes: Record<string, string | null>) {
    const next = new URLSearchParams(params)
    for (const [k, v] of Object.entries(changes)) {
      if (v === null || v === '') next.delete(k)
      else next.set(k, v)
    }
    if (!('page' in changes)) next.delete('page') // 篩選條件改變就回第一頁
    setParams(next)
  }

  const hasNext = (list.data?.length ?? 0) === PAGE_SIZE
  const hasFilter = errorType || q || from || to || includeDismissed

  return (
    <>
      <h1>句子列表</h1>

      <form
        className="filters"
        onSubmit={(e) => {
          e.preventDefault()
          const fd = new FormData(e.currentTarget)
          update({ q: String(fd.get('q') ?? '') })
        }}
      >
        <label>
          錯誤類型
          <select value={errorType} onChange={(e) => update({ error_type: e.target.value })}>
            <option value="">全部</option>
            {types.data?.map((t) => (
              <option key={t.id} value={t.name}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          從
          <input type="date" value={from} max={to || undefined} onChange={(e) => update({ from: e.target.value })} />
        </label>
        <label>
          到
          <input type="date" value={to} min={from || undefined} onChange={(e) => update({ to: e.target.value })} />
        </label>
        <label>
          關鍵字
          <input name="q" type="search" defaultValue={q} key={q} placeholder="比對原句與修正句" />
        </label>
        <button type="submit" className="btn">
          搜尋
        </button>
        <label className="checkbox">
          <input type="checkbox" checked={includeDismissed} onChange={(e) => update({ include_dismissed: e.target.checked ? '1' : null })} />
          顯示已標記誤判
        </label>
        {hasFilter && (
          <button type="button" className="btn btn-ghost" onClick={() => setParams(new URLSearchParams())}>
            清除篩選
          </button>
        )}
      </form>

      {list.isPending && <Loading />}
      {list.error && <ErrorBox error={list.error} />}
      {list.data && list.data.length === 0 && <Empty>{page > 1 ? '這一頁沒有資料' : '沒有符合的句子'}</Empty>}
      {list.data && list.data.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>#</th>
              <th>時間</th>
              <th>原句</th>
              <th>錯誤類型</th>
              <th>來源</th>
            </tr>
          </thead>
          <tbody>
            {list.data.map((s) => (
              <tr key={s.id} className={s.is_dismissed ? 'dismissed' : undefined}>
                <td className="muted">{s.id}</td>
                <td className="nowrap muted">{formatDateTime(s.created_at)}</td>
                <td>
                  <Link to={`/sentences/${s.id}`}>{s.original_text}</Link>
                  {s.is_dismissed && <span className="chip chip-muted">誤判</span>}
                </td>
                <td>
                  <ErrorTypeChips sentence={s} />
                </td>
                <td>
                  <SourceBadge source={s.source} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="pager">
        <button type="button" className="btn btn-ghost" disabled={page <= 1} onClick={() => update({ page: String(page - 1) })}>
          ← 上一頁
        </button>
        <span className="muted">第 {page} 頁</span>
        <button type="button" className="btn btn-ghost" disabled={!hasNext} onClick={() => update({ page: String(page + 1) })}>
          下一頁 →
        </button>
      </div>
    </>
  )
}
