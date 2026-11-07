# 04. 正式版 docker-compose 與啟動

## 目標

在 Lightsail 上用 `docker-compose.prod.yml` build 並啟動五個容器（db、backend、mcp、frontend、caddy），確認都 healthy。

## 前置條件

- [03](03-server-setup.md) 完成。
- 本機 `docker compose --profile http --profile prod up` 已能正常運作（steps/09）。

## 步驟

### 4-1. 建立 `docker-compose.prod.yml` 與暫時版 Caddyfile

檔案內容**與 Hostinger 版完全相同**（程式與 compose 不分平台），請照
[hostinger/03-compose-prod.md](../hostinger/03-compose-prod.md) 的 3-1、3-2、3-3 建立：

- `docker-compose.prod.yml`：不掛原始碼、不開 `--reload`、只有 caddy 開 80/443、全部 `restart: unless-stopped`。
- 程式端小修改：`CORS_ORIGINS` 環境變數、frontend Dockerfile 的 `VITE_API_URL` build arg、前端移除 `VITE_API_KEY`。
- `deploy/Caddyfile`：先用 `:80` 的暫時版（05 再換網域）。

先在本機 `docker compose -f docker-compose.prod.yml config` 檢查語法再 commit。

### 4-2. 在 Lightsail 上 build 與啟動

```bash
sudo -i
cd /srv/english-tutor
git pull
docker compose -f docker-compose.prod.yml build      # 第一次約 3–5 分鐘，2 vCPU 比 Hostinger KVM 1 快
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps          # 五個都 Up / healthy
docker compose -f docker-compose.prod.yml exec backend uv run alembic upgrade head
```

> build 時 Lightsail 的 CPU 會短暫跑到 100%，這會消耗 burst capacity（實例頁 Metrics 看得到）。
> $12 方案平常閒置時會累積，偶爾 build 沒問題；若 build 過程被 OOM kill，先確認 03 的 swap 有開。

### 4-3. 驗證

機器上：

```bash
curl -s http://localhost/api/docs | head -5                       # FastAPI Swagger HTML
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/mcp     # 401（沒帶 key）
curl -s http://localhost/ | grep -o "<title>.*</title>"           # 前端 index.html
docker compose -f docker-compose.prod.yml logs --tail 50 backend
```

確認沒有多開 port：

```bash
ss -tlnp | grep -E ':(5432|8000|8001|3000|8080)\b' || echo "OK: nothing exposed"
```

本機瀏覽器開 `http://<STATIC_IP>/` 應看到前端（API 還不通，05 設好網域後才會）。

### 4-4. 限制 Docker log 大小（60 GB 磁碟時先做比較安心，80 GB 也建議）

```bash
cat > /etc/docker/daemon.json <<'JSON'
{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
JSON
systemctl restart docker
docker compose -f docker-compose.prod.yml up -d
```

## 完成條件

- [x] `docker compose -f docker-compose.prod.yml ps` 五個服務 Up，db healthy（db、backend、mcp 皆 healthy）
- [x] `ss -tlnp` 只看到 22、80、443
- [x] `http://<STATIC_IP>/api/docs` 可開（原 http://44.228.11.180/api/docs，現為 http://35.79.82.165/api/docs）
- [x] `/mcp` 沒帶 key 回 401
- [x] `docker-compose.prod.yml` 與 `deploy/Caddyfile` 已 commit（f7edba0）

## 下一步

→ [05-domain-caddy-https.md](05-domain-caddy-https.md)

## 實作紀錄

**2026-11-02**（透過 cmux 裡已登入的 SSH 面板操作，完整敘述見 [local-to-lightsail.md](local-to-lightsail.md)）

- `docker-compose.prod.yml` 與 hostinger 範本的差異：frontend 不用 `VITE_API_URL` build arg（step 08 已改成相對路徑 `/api` 由 nginx 代理並注入 key），所以 `deploy/Caddyfile` 只有 `/mcp*` → mcp 與其餘 → frontend 兩段；backend `command` 含 `alembic upgrade head`，不必另外 exec。
- build 48.9 秒（文件估 3–5 分鐘，2 vCPU 快很多），`up -d` 後 30 秒五個容器就緒。
- 機器上 `curl` 驗證與 Mac 端用公開 IP 驗證結果一致；8000/8001/5432 從外部連不到。
- 4-4 的 `daemon.json` 已套用（json-file、10m × 3），restart docker 後需再 `up -d`。
- 尚未重開機（登入訊息仍顯示 restart required），留待使用者方便時執行並順便驗證 `restart: unless-stopped`。
