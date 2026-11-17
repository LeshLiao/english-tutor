from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Docker FastAPI Demo")

# 瀏覽器從 http://localhost:8082（React 前端）呼叫本 API 時，
# 來源（origin）不同，必須明確允許，否則瀏覽器會擋下回應（CORS）。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8082", "http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

TAIPEI = timezone(timedelta(hours=8))


@app.get("/")
def root():
    return {"message": "Hello from FastAPI in Docker 🐳", "try": "/date"}


@app.get("/date")
def get_date():
    """回傳現在日期與時間（台北時區）。"""
    now = datetime.now(TAIPEI)
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": now.strftime("%A"),
        "iso": now.isoformat(),
    }
