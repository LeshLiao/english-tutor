import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api, formatDateTime, type TrendPoint } from '../api'
import { Empty, ErrorBox, ErrorTypeChips, Loading, SourceBadge } from '../components'

const TREND_DAYS = 30

function isoDaysAgo(days: number): string {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() - days)
  return d.toISOString()
}

/** 後端只回有資料的日期；折線圖要連續，所以把沒資料的日子補 0。 */
function fillDays(points: TrendPoint[], days: number): TrendPoint[] {
  const byDay = new Map(points.map((p) => [p.period, p]))
  const out: TrendPoint[] = []
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() - days)
  for (let i = 0; i <= days; i++) {
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    out.push(byDay.get(key) ?? { period: key, sentence_count: 0, error_count: 0 })
    d.setDate(d.getDate() + 1)
  }
  return out
}

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

export default function Overview() {
  const stats = useQuery({ queryKey: ['stats', 'errors'], queryFn: () => api.errorStats() })
  const trend = useQuery({
    queryKey: ['stats', 'trend', TREND_DAYS],
    queryFn: () => api.trend({ interval: 'day', from: isoDaysAgo(TREND_DAYS) }),
  })
  const recent = useQuery({ queryKey: ['sentences', 'recent'], queryFn: () => api.sentences({ limit: 5 }) })

  const totalErrors = stats.data?.reduce((s, r) => s + r.count, 0) ?? 0
  const trendData = trend.data ? fillDays(trend.data, TREND_DAYS) : []
  const sentences30d = trendData.reduce((s, p) => s + p.sentence_count, 0)
  const errors30d = trendData.reduce((s, p) => s + p.error_count, 0)

  const series1 = cssVar('--series-1')
  const series2 = cssVar('--series-2')
  const ink = cssVar('--text-secondary')
  const grid = cssVar('--grid')

  return (
    <>
      <h1>總覽</h1>

      <section className="tiles">
        <div className="tile">
          <div className="tile-label">錯誤類型</div>
          <div className="tile-value">{stats.data?.length ?? '–'}</div>
        </div>
        <div className="tile">
          <div className="tile-label">錯誤總數</div>
          <div className="tile-value">{stats.data ? totalErrors : '–'}</div>
        </div>
        <div className="tile">
          <div className="tile-label">最近 {TREND_DAYS} 天句子</div>
          <div className="tile-value">{trend.data ? sentences30d : '–'}</div>
        </div>
        <div className="tile">
          <div className="tile-label">最近 {TREND_DAYS} 天錯誤</div>
          <div className="tile-value">{trend.data ? errors30d : '–'}</div>
        </div>
      </section>

      <section className="card">
        <h2>各錯誤類型次數</h2>
        {stats.isPending && <Loading />}
        {stats.error && <ErrorBox error={stats.error} />}
        {stats.data && stats.data.length === 0 && <Empty>還沒有任何錯誤紀錄</Empty>}
        {stats.data && stats.data.length > 0 && (
          <div style={{ height: 40 + stats.data.length * 36 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.data} layout="vertical" margin={{ top: 4, right: 32, bottom: 4, left: 8 }}>
                <CartesianGrid horizontal={false} stroke={grid} />
                <XAxis type="number" allowDecimals={false} tick={{ fill: ink, fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="error_type" width={170} tick={{ fill: ink, fontSize: 13 }} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: grid }} formatter={(v) => [v, '次數']} />
                <Bar dataKey="count" name="次數" fill={series1} radius={[0, 4, 4, 0]} barSize={20} label={{ position: 'right', fill: ink, fontSize: 12 }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section className="card">
        <h2>最近 {TREND_DAYS} 天趨勢</h2>
        {trend.isPending && <Loading />}
        {trend.error && <ErrorBox error={trend.error} />}
        {trend.data && (
          <div style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 8, right: 16, bottom: 4, left: -16 }}>
                <CartesianGrid vertical={false} stroke={grid} />
                <XAxis dataKey="period" tickFormatter={(d: string) => d.slice(5)} tick={{ fill: ink, fontSize: 12 }} axisLine={false} tickLine={false} minTickGap={24} />
                <YAxis allowDecimals={false} tick={{ fill: ink, fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="sentence_count" name="句子數" stroke={series1} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                <Line type="monotone" dataKey="error_count" name="錯誤數" stroke={series2} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section className="card">
        <div className="card-head">
          <h2>最近 5 筆句子</h2>
          <Link to="/sentences">看全部 →</Link>
        </div>
        {recent.isPending && <Loading />}
        {recent.error && <ErrorBox error={recent.error} />}
        {recent.data && recent.data.length === 0 && <Empty>還沒有任何句子</Empty>}
        {recent.data && recent.data.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>時間</th>
                <th>原句</th>
                <th>錯誤類型</th>
                <th>來源</th>
              </tr>
            </thead>
            <tbody>
              {recent.data.map((s) => (
                <tr key={s.id}>
                  <td className="nowrap muted">{formatDateTime(s.created_at)}</td>
                  <td>
                    <Link to={`/sentences/${s.id}`}>{s.original_text}</Link>
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
      </section>
    </>
  )
}
