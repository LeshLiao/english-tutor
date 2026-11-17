import { useEffect, useState } from 'react'

// 後端 API 位址。瀏覽器是在 Mac 上跑，所以要打 Mac 對外的 8083 port，
// 而不是容器內部的 8000。
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8083'

function App() {
  const [count, setCount] = useState(0)
  const [today, setToday] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/date`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(setToday)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <main className="card">
      <h1>Hello from Docker 🐳</h1>
      <p>這是一個用 Vite + React 建置，在 Node 容器裡用 vite preview 提供的靜態網頁。</p>

      <section className="date">
        <h2>後端回傳的日期</h2>
        {error && <p className="error">呼叫 API 失敗：{error}</p>}
        {!error && !today && <p>載入中…</p>}
        {today && (
          <p>
            {today.date}（{today.weekday}） {today.time}
          </p>
        )}
        <small>來源：{API_URL}/date</small>
      </section>

      <button onClick={() => setCount((c) => c + 1)}>
        你已經點了 {count} 次
      </button>
    </main>
  )
}

export default App
