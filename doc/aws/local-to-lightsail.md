# 從本機到 Lightsail：這次部署實際做了什麼

> 2026-11-02 由 Claude Code 在 cmux 裡完成。本機步驟在 Mac 的終端機執行，遠端步驟全部透過 cmux 已經 SSH 上 Lightsail 的那個面板（`ubuntu@ip-172-26-0-82`）送指令並讀回畫面，沒有另外開 SSH 連線。
> 這份文件是「做了什麼、為什麼」的敘述版；逐步操作手冊仍以 [03-server-setup.md](03-server-setup.md) 與 [04-compose-prod.md](04-compose-prod.md) 為準。

## 一張圖看懂

```
Mac（本機開發）                          GitHub                    Lightsail 44.228.11.180（Ubuntu 24.04, 2 vCPU / 2 GB）
────────────────                        ──────                    ─────────────────────────────────────────────────
docker-compose.yml（開發用）                                       /srv/english-tutor（git clone）
docker-compose.prod.yml  ──commit──▶  LeshLiao/        ──clone──▶   .env（伺服器上用 openssl 隨機產生，不在 git 裡）
deploy/Caddyfile            push       english-tutor                 docker compose -f docker-compose.prod.yml up -d
                                                                       ├── caddy     :80/:443 ← 唯一對外的容器
                                                                       ├── frontend  nginx：靜態檔 + /api/* → backend（注入 X-API-Key）
                                                                       ├── mcp       :8001  Streamable HTTP，自己驗 X-API-Key
                                                                       ├── backend   :8000  FastAPI，啟動時先 alembic upgrade head
                                                                       └── db        :5432  PostgreSQL 16，資料在 volume pgdata
```

程式碼**完全沒有為了上雲而改**。本機 step 01–09 做出來的三個映像（backend、mcp、frontend）在雲端原樣 build，只換兩個部署檔與一份 `.env`。

## 第 1 段：本機準備（Mac）

### 1-1. 確認本機版本都跑得起來

- `doc/mac-step` 的 01–09 全部完成：後端、MCP（HTTP 模式）、前端容器版都已在本機以 `docker compose --profile http --profile prod up` 驗證過。
- 這是上雲的前提：雲端只是把同樣的東西換台機器跑。

### 1-2. 新增兩個部署檔

`docker-compose.prod.yml`（repo 根目錄）

- 從開發版複製而來，差異只有：
  - **不掛原始碼、不 `--reload`**：程式碼 build 進映像。
  - **只有 caddy 有 `ports:`**（80/443）；db、backend、mcp、frontend 都只在 Docker 內網互通。
  - **全部 `restart: unless-stopped`**：機器重開後自動起來。
  - **沒有 adminer**：要看資料庫用 SSH tunnel 或 `psql`。
  - backend 的 `command` 是 `alembic upgrade head && uvicorn ...`，每次啟動自動套 migration。
  - 不用 profiles，五個服務都是正式服務。
- 本機先 `docker compose -f docker-compose.prod.yml config` 檢查語法。

`deploy/Caddyfile`（暫時版，只用 IP、HTTP 80）

```
:80 {
    encode gzip
    handle /mcp* { reverse_proxy mcp:8001 }
    handle       { reverse_proxy frontend:80 }
}
```

- 跟 hostinger 文件的範本比，**少了 `/api/*` 那段**：因為 step 08 的 frontend 容器本身就是 nginx，已經會把 `/api/*` 代理到 backend 並注入 `X-API-Key`，Caddy 不用再做一次。
- `/mcp*` 直通 mcp 容器，由 mcp 自己驗 key（Claude Code 連線時自帶）。

### 1-3. 推上 GitHub

本機 main 當時領先 origin 五個 commit（step 07–09 的成果），伺服器要 clone 得到程式碼，所以：

```bash
git add docker-compose.prod.yml deploy/Caddyfile
git commit -m "Add production docker-compose and temporary Caddyfile for single-host deployment"
git push origin main        # f7edba0
```

repo 是公開的，伺服器用 https clone 即可，不需要 deploy key。

## 第 2 段：Lightsail 上的操作（透過 cmux 面板）

每一步都是 `cmux send --surface surface:21 '<指令>'` 送進面板、`cmux send-key Enter`，再用 `cmux read-screen` 讀畫面。長時間的步驟（build）在指令尾端加一個 `===XXX DONE===` 標記，每 10 秒讀一次畫面直到看到標記。

### 2-1. 環境檢查

```bash
id; docker --version; docker compose version; ls -la /srv; free -h; df -h /; swapon --show
```

結果：ubuntu 已在 `docker` 群組（不用 sudo 跑 docker）、Docker 29.9 / Compose v5.6、`/srv` 空的、2 GB swap 已掛、磁碟剩 51 GB。03 的前半段（更新、swap、時區）確實已在 11-01 做好。

### 2-2. 建目錄並 clone

```bash
sudo mkdir -p /srv/english-tutor && sudo chown ubuntu:ubuntu /srv/english-tutor
cd /srv/english-tutor && git clone https://github.com/LeshLiao/english-tutor.git .
```

選擇讓目錄歸 ubuntu 而不是 root：之後 `git pull` 不用 sudo，docker 也不用 sudo，整個更新流程可以用一般帳號完成。

### 2-3. 產生正式版 `.env`

```bash
printf "POSTGRES_USER=english\nPOSTGRES_PASSWORD=%s\nPOSTGRES_DB=english_practice\nAPI_KEY=%s\nCORS_ORIGINS=\nDOMAIN=\n" \
  "$(openssl rand -base64 24 | tr -d /+=)" "$(openssl rand -hex 32)" > .env
chmod 600 .env
```

- 密碼與 API key 在伺服器上隨機產生，整個過程**沒有把值印在畫面上**，只印了變數名稱與 key 長度（64）。
- `CORS_ORIGINS` 留空：前端與 API 同源（都走 Caddy → nginx），不需要 CORS。
- `DOMAIN` 留空：05 設網域時再填。
- 之後 Claude Code 要連雲端 MCP（06）時，用 `ssh english-tutor 'grep ^API_KEY= /srv/english-tutor/.env'` 取 key。

### 2-4. Build 與啟動

```bash
docker compose -f docker-compose.prod.yml build     # 48.9 秒，無錯誤
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
```

- 2 vCPU 的 build 比預期快很多（文件估 3–5 分鐘）。frontend 的 `npm ci` + `vite build` 是最重的一段，沒有碰到 OOM。
- `up -d` 後約 30 秒：db、backend、mcp 都 healthy，frontend 與 caddy Up。

### 2-5. 驗證（機器上）

| 檢查 | 指令 | 結果 |
|------|------|------|
| 前端 | `curl -s http://localhost/ \| grep -o "<title>.*</title>"` | `English Tutor` |
| Swagger | `curl -s http://localhost/api/docs \| grep -o "<title>.*</title>"` | `English Tutor API - Swagger UI` |
| 後端健康 | `curl -s http://localhost/api/health` | `{"status":"ok","database":"ok"}` |
| MCP 無 key | `curl -o /dev/null -w "%{http_code}" http://localhost/mcp` | 401 |
| MCP 正確 key | `curl -X POST http://localhost/mcp -H "X-API-Key: $(grep ^API_KEY= .env \| cut -d= -f2)" ... tools/list` | 200 |
| 對外監聽 | `sudo ss -tlnp` | 只有 22、80、443（其餘是 127.0.0.1 的系統服務） |

### 2-6. Docker log 輪替（04-4）

```bash
echo '{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
docker compose -f docker-compose.prod.yml up -d
```

restart docker 會把容器全部停掉，所以要再 `up -d` 一次；20 秒後五個都回來。

## 第 3 段：從 Mac 端用公開 IP 驗證

```bash
curl -s http://44.228.11.180/ | grep -o "<title>.*</title>"      # English Tutor
curl -s http://44.228.11.180/api/health                           # {"status":"ok","database":"ok"}
curl -s http://44.228.11.180/api/stats/errors                     # []（新資料庫，還沒有句子）
curl -o /dev/null -w "%{http_code}" http://44.228.11.180/mcp      # 401
curl -m 3 http://44.228.11.180:8000/  # 連不上：Lightsail 防火牆只開 22/80/443，8001、5432 同樣擋住
```

## 目前狀態與還沒做的事

**已完成**：aws 03（含 3-4、3-5）、aws 04 全部完成條件。瀏覽器開 http://44.228.11.180/ 可以看到前端，資料庫是空的。

**要注意**

- **現在任何人開這個 IP 都能看到前端並透過它呼叫 API**（nginx 代為注入 key）。資料只是英文句子，但 05 的 basic auth 做好之前，不要把 IP 貼給別人。`/mcp` 不受影響，一直都要 key。
- 伺服器登入訊息顯示 `*** System restart required ***`（11-01 更新 kernel 後尚未重開）。找個時間 `sudo reboot`，順便驗證 `restart: unless-stopped` 會把五個容器帶起來。這次沒有重開，因為會中斷 cmux 裡那個 SSH 面板。
- 雲端資料庫是全新的，本機的句子沒有搬過去。要的話在本機 `pg_dump`、在伺服器 `psql` 匯入（07 的備份機制可以反過來用）。

**下一步**：[05-domain-caddy-https.md](05-domain-caddy-https.md)（網域、HTTPS、basic auth）→ [06-claude-connect.md](06-claude-connect.md)（Claude Code 改連 `https://<domain>/mcp`）→ [07-backup-monitor.md](07-backup-monitor.md)。

## 之後怎麼更新一版

```bash
# Mac
git push origin main
# Lightsail（cmux 面板或 ssh english-tutor）
cd /srv/english-tutor && git pull && docker compose -f docker-compose.prod.yml up -d --build
```

只重 build 有變動的映像，migration 由 backend 啟動時自動套用。詳見 [08-update-cicd.md](08-update-cicd.md)。
