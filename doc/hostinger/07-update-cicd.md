# 07. 更新流程與自動部署（選用）

## 目標

一條指令更新到最新版；選用 GitHub Actions 在 push 到 `main` 時自動部署。

## 前置條件

- [06](06-backup-monitor.md) 完成。

## 步驟

### 7-1. 手動更新（基本款）

`deploy/update.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /srv/english-tutor
git pull --ff-only
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec -T backend uv run alembic upgrade head
docker image prune -f
docker compose -f docker-compose.prod.yml ps
```

```bash
chmod +x deploy/update.sh
./deploy/update.sh
```

> 有資料表變更的版本，更新前先 `./deploy/backup.sh`，並到 hPanel 拍一張快照。

### 7-2. 從本機一鍵觸發

```powershell
ssh root@<VPS_IP> /srv/english-tutor/deploy/update.sh
```

### 7-3. GitHub Actions 自動部署（選用）

VPS 上建一把專用金鑰，公鑰加進 `~/.ssh/authorized_keys`，私鑰放 GitHub repo → Settings → Secrets：

| Secret | 值 |
|--------|----|
| `VPS_HOST` | VPS IP |
| `VPS_SSH_KEY` | 私鑰內容 |

`.github/workflows/deploy.yml`：

```yaml
name: deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: root
          key: ${{ secrets.VPS_SSH_KEY }}
          script: /srv/english-tutor/deploy/update.sh
```

> 這是最簡單的做法：在 VPS 上 build。若 1 vCPU build 太慢，進階做法是 Actions 先 build 映像推到 GHCR，
> `docker-compose.prod.yml` 改成 `image: ghcr.io/<帳號>/english-backend:latest`，VPS 只 `pull` 不 `build`。

### 7-4. Hostinger Docker Manager（可選的另一條路）

hPanel → VPS → Docker Manager 可以直接貼 `docker-compose.prod.yml` 或指向公開 repo 的 URL，
在網頁上看容器狀態與日誌，不用 SSH。

限制：

- 官方文件只提到公開 repo；私有 repo 要用貼 YAML 的方式。
- 文件沒有說明 `build:` 與 build `args:` 的支援程度；若不行，就改用 7-3 的 GHCR 映像。
- `.env` 的變數要在 Docker Manager 介面另外填。

建議先用 SSH + `update.sh` 跑穩，Docker Manager 當作看狀態的儀表板就好。

### 7-5. 回滾

```bash
cd /srv/english-tutor
git log --oneline -5
git checkout <上一版 commit>
docker compose -f docker-compose.prod.yml up -d --build
```

資料表有變更時，先 `alembic downgrade -1` 再切版本；或直接用 06 的備份還原。

## 完成條件

- [ ] `./deploy/update.sh` 一次跑完無錯誤
- [ ] 改一行前端文字 push 後，網站在 5 分鐘內更新（手動或 Actions）
- [ ] 練習過一次回滾

## 下一步

全部完成後回到 [總覽](00-README.md) 勾選完成條件。之後若流量或功能成長，再考慮 [steps/10-aws-deploy.md](../steps/10-aws-deploy.md) 的階段 B。

## 實作紀錄

（填寫日期、遇到的問題與解法）
