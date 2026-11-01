# 06. 備份、日誌與監控

## 目標

資料庫每天自動 `pg_dump`、保留 14 天並下載一份到本機；開 Hostinger 快照；知道去哪看日誌；壞掉會收到通知。

## 前置條件

- [05](05-claude-connect.md) 完成，資料庫已有真實資料。

## 步驟

### 6-1. 每日 pg_dump

`deploy/backup.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /srv/english-tutor
mkdir -p /srv/backups
STAMP=$(date +%Y%m%d-%H%M)
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom \
  > "/srv/backups/english_${STAMP}.dump"
find /srv/backups -name '*.dump' -mtime +14 -delete
```

```bash
chmod +x deploy/backup.sh
set -a; source .env; set +a; ./deploy/backup.sh      # 手動跑一次
ls -lh /srv/backups
```

排程（每天 03:30 台灣時間）：

```bash
crontab -e
```

```
30 3 * * * cd /srv/english-tutor && set -a && . ./.env && set +a && ./deploy/backup.sh >> /var/log/english-backup.log 2>&1
```

### 6-2. 還原測試（一定要做一次）

```bash
docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore -U english -d english_practice --clean --if-exists < /srv/backups/english_<最新>.dump
```

接著前端重新整理，資料仍在，就算通過。

### 6-3. 備份下載到本機（離站備份）

每週在本機跑一次：

```powershell
scp root@<VPS_IP>:/srv/backups/english_*.dump D:\backups\english-tutor\
```

或用 Windows 工作排程器排程。VPS 的磁碟壞掉時，這份才是真正的保險。

### 6-4. Hostinger 快照

hPanel → VPS → Backups & Snapshots：

- **Backups**：KVM 方案內含每週自動備份，確認是 On。
- **Snapshot**：每次大改（升級 Postgres 版本、改 compose）前手動拍一張；只能存一張，會覆蓋。

### 6-5. 日誌

```bash
docker compose -f docker-compose.prod.yml logs -f --tail 100 backend
docker compose -f docker-compose.prod.yml logs -f --tail 100 mcp
docker compose -f docker-compose.prod.yml logs --since 1h caddy | grep -v '"status":200'
```

Hook 是否真的有寫入：看 backend log 有 `POST /sentences 201`。

限制 log 大小，避免磁碟被吃滿（`/etc/docker/daemon.json`）：

```json
{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
```

```bash
systemctl restart docker && docker compose -f docker-compose.prod.yml up -d
```

### 6-6. 監控

- **外部存活監控**：UptimeRobot（免費）每 5 分鐘打 `https://<domain>/api/health`（backend 加一個不需 key 的 `/health` 路由，Caddy 的 basic auth 清單把它排除）。掛了寄 email。
- **資源**：hPanel → VPS 概覽有 CPU / RAM / 磁碟 / 流量圖；機器內 `docker stats`、`df -h`。
- **磁碟警戒**：50 GB 對這個專案很夠，但 Docker build cache 會累積，每月跑一次 `docker system prune -f`。

## 完成條件

- [ ] `/srv/backups` 每天多一個 dump，14 天後自動刪
- [ ] 還原測試成功一次
- [ ] 本機有至少一份離站備份
- [ ] hPanel 自動備份 On
- [ ] UptimeRobot 監控建立，故意 `docker compose stop backend` 有收到通知

## 下一步

→ [07-update-cicd.md](07-update-cicd.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）
