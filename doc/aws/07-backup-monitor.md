# 07. 備份、快照、日誌與監控

## 目標

資料庫每天自動 `pg_dump` 並上傳 S3（30 天自動刪除）；Lightsail 每日自動快照；機器掛掉或 CPU 爆掉會收到 email。

## 前置條件

- [06](06-claude-connect.md) 完成，資料庫已有真實資料。

## 步驟

### 7-1. 建 S3 bucket 與生命週期

S3 → Create bucket：

| 欄位 | 值 |
|------|----|
| 名稱 | `english-tutor-backup-<隨機字串>`（全球唯一） |
| 區域 | Tokyo ap-northeast-1（與實例同區，傳輸免費；2026-11-07 前為 Oregon us-west-2） |
| Block all public access | 保持勾選 |
| Versioning | 關閉（dump 檔本身就有時間戳） |

建好後 → Management → Lifecycle rules → Create：套用整個 bucket，**Expire current versions after 30 days**。

費用：dump 檔幾 MB，30 份合計不到 1 GB，S3 標準儲存約 $0.025/GB/月，可忽略。

### 7-2. 備份專用 IAM 使用者（權限只限這個 bucket）

Lightsail 實例不能掛 IAM role，所以要用 access key。
IAM → Users → Create user `english-backup`，不開 Console access，Attach policy → Create inline policy（JSON）：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::english-tutor-backup-<隨機字串>",
        "arn:aws:s3:::english-tutor-backup-<隨機字串>/*"
      ]
    }
  ]
}
```

建立後 → Security credentials → Create access key（用途選 Other），記下 Access key ID 與 Secret。

### 7-3. 機器上裝 AWS CLI 並設定

```bash
sudo -i
snap install aws-cli --classic
aws --version
aws configure            # 填 access key、secret、region ap-northeast-1、output json
aws s3 ls s3://english-tutor-backup-<隨機字串>/   # 空的，但不能是 AccessDenied
```

> 不要在這台機器上放 Administrator 等級的 key；這把 key 只能寫這個 bucket，外洩影響有限。

### 7-4. 每日 pg_dump + 上傳

`deploy/backup.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /srv/english-tutor
mkdir -p /srv/backups
STAMP=$(date +%Y%m%d-%H%M)
FILE="/srv/backups/english_${STAMP}.dump"
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom > "$FILE"
aws s3 cp "$FILE" "s3://${BACKUP_BUCKET}/" --only-show-errors
find /srv/backups -name '*.dump' -mtime +7 -delete       # 本機只留 7 天，S3 留 30 天
```

`.env` 加一行 `BACKUP_BUCKET=english-tutor-backup-<隨機字串>`。

```bash
chmod +x deploy/backup.sh
set -a; source .env; set +a; ./deploy/backup.sh      # 手動跑一次
ls -lh /srv/backups
aws s3 ls s3://$BACKUP_BUCKET/
```

排程（每天 03:30 台灣時間）：

```bash
crontab -e
```

```
30 3 * * * cd /srv/english-tutor && set -a && . ./.env && set +a && ./deploy/backup.sh >> /var/log/english-backup.log 2>&1
```

### 7-5. 還原測試（一定要做一次）

```bash
aws s3 cp s3://$BACKUP_BUCKET/english_<最新>.dump /tmp/restore.dump
docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore -U english -d english_practice --clean --if-exists < /tmp/restore.dump
```

接著前端重新整理，資料仍在，就算通過。

### 7-6. Lightsail 自動快照

實例頁 → Snapshots → Automatic snapshots → Enable，時間選 UTC 19:00（台灣 03:00，在 pg_dump 之前）。
保留 7 天，自動輪替。

費用 $0.05/GB/月，只算實際使用的磁碟（約 5–10 GB），每月約 $0.25–0.50。
每次大改（升級 Postgres 版本、改 compose）前再手動拍一張。

> 快照是整台機器的保險，S3 的 dump 是資料的保險。機器壞掉從快照開新實例（幾分鐘）；資料誤刪從 dump 還原。

### 7-7. 警報（Lightsail 內建，免費）

實例頁 → Metrics → 各指標 → Add alarm：

| 指標 | 條件 | 說明 |
|------|------|------|
| Status check failed | ≥ 1，連續 2 次（10 分鐘） | 機器掛了 |
| CPU utilization | ≥ 80%，連續 3 次（15 分鐘） | 可能卡死或被打 |
| Burstable capacity (percentage) | ≤ 20%，連續 1 次 | CPU 點數快用完，會被降速 |

Notifications → Email，第一次要到信箱點確認連結。

**外部存活監控**：UptimeRobot（免費）每 5 分鐘打 `https://<domain>/api/health`
（backend 加一個不需 key 的 `/health` 路由，Caddy 的 basic auth 清單把它排除）。
Lightsail 警報看的是機器，UptimeRobot 看的是服務，兩個都要。

### 7-8. 日誌

```bash
docker compose -f docker-compose.prod.yml logs -f --tail 100 backend
docker compose -f docker-compose.prod.yml logs -f --tail 100 mcp
docker compose -f docker-compose.prod.yml logs --since 1h caddy | grep -v '"status":200'
```

Hook 是否真的有寫入：看 backend log 有 `POST /sentences 201`。
log 大小已在 04-4 限制；每月跑一次 `docker system prune -f` 清 build cache。

## 完成條件

- [ ] S3 每天多一個 dump，lifecycle 30 天
- [ ] 還原測試成功一次
- [ ] 自動快照 Enabled，看到第一張
- [ ] Lightsail 三條警報建立，email 已確認
- [ ] UptimeRobot 監控建立，故意 `docker compose stop backend` 有收到通知

## 下一步

→ [08-update-cicd.md](08-update-cicd.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）
