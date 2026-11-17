# Docker 練習：前端 + 後端

| 目錄 | 內容 | Mac port |
|------|------|----------|
| `frontend/` | Vite + React，網頁載入時呼叫後端 `/date` | 8082 |
| `backend/`  | FastAPI，`GET /date` 回傳今天日期 | 8083 |

## 一次啟動兩個容器（docker compose）

在本目錄執行：

```bash
docker compose up --build -d
```

開 <http://localhost:8082>，網頁會顯示後端回傳的日期。

看狀態與 log：

```bash
docker compose ps
```

```bash
docker compose logs -f
```

全部停止並移除容器：

```bash
docker compose down
```

## compose 檔的幾個重點

- `services` 底下每一個名字就是一個容器，這裡有 `backend` 與 `frontend`。
- `build: ./backend` 等於 `docker build ./backend`；`ports: "8083:8000"` 等於 `docker run -p 8083:8000`。
- `depends_on` 只保證啟動順序，不會等後端「準備好」才起前端。
- `docker compose up` 會自動建立一個內部網路，容器之間可以用服務名互相連線（例如在容器內 `http://backend:8000`）。
  不過本範例的前端 JavaScript 是在瀏覽器執行，所以它打的仍是 Mac 的 `localhost:8083`。

## 分開跑（不用 compose）

各目錄的 README 有純 `docker build` / `docker run` 指令。
