# 單階段：一個 Python 映像安裝依賴並啟動 FastAPI
FROM python:3.12-slim

WORKDIR /app

# 先複製 requirements.txt 再安裝，讓 pip install 這層能被 Docker 快取
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再複製程式碼
COPY main.py .

# uvicorn 預設監聽 8000；--host 0.0.0.0 讓容器外面連得進來
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
