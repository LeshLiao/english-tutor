# Docker + FastAPI 範例

最小可行的後端範例：一個 Python 容器跑 FastAPI，提供回傳現在日期的 API。

## 檔案說明

| 檔案 | 用途 |
|------|------|
| `main.py` | FastAPI 程式，兩個路由：`/` 與 `/date` |
| `requirements.txt` | Python 依賴（fastapi、uvicorn） |
| `Dockerfile` | 單階段：安裝依賴 → 用 uvicorn 啟動 |
| `.dockerignore` | 排除 `__pycache__`、`.venv` 等，縮小 build context |

## 使用方式（純 docker 指令）

在本目錄下建置映像：

```bash
docker build -t docker-fastapi-demo .
```

啟動容器（本機 8083 對應容器內 8000）：

```bash
docker run --rm -p 8083:8000 docker-fastapi-demo
```

按 `Ctrl+C` 停止。若想在背景跑：

```bash
docker run -d --rm --name docker-fastapi-demo -p 8083:8000 docker-fastapi-demo
```

```bash
docker stop docker-fastapi-demo
```

## 呼叫 API

```bash
curl http://localhost:8083/date
```

回傳範例：

```json
{"date":"2026-11-17","time":"14:30:00","weekday":"Monday","iso":"2026-11-17T14:30:00+08:00"}
```

FastAPI 內建的互動式文件：<http://localhost:8083/docs>

## 本機開發（不用 Docker）

```bash
uv venv && uv pip install -r requirements.txt
```

```bash
uv run uvicorn main:app --reload
```

## CORS

`main.py` 加了 `CORSMiddleware`，允許來源 `http://localhost:8082`（React 前端容器）
與 `http://localhost:5173`（Vite 本機開發）。
瀏覽器跨來源呼叫 API 時，沒有這段會被擋下，用 curl 則不受影響。
