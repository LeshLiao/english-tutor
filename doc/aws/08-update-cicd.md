# 08. 更新流程與自動部署（選用）

## 目標

一條指令更新到最新版；選用 GitHub Actions 在 push 到 `main` 時自動部署。

## 前置條件

- [07](07-backup-monitor.md) 完成。

## 步驟

### 8-1. 手動更新（基本款）

`deploy/update.sh` 與 [hostinger/07-update-cicd.md](../hostinger/07-update-cicd.md) 的 7-1 相同：

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
sudo /srv/english-tutor/deploy/update.sh
```

> 有資料表變更的版本，更新前先 `./deploy/backup.sh`，並在 Lightsail 手動拍一張快照。

### 8-2. 從本機一鍵觸發

```powershell
ssh ubuntu@<STATIC_IP> sudo /srv/english-tutor/deploy/update.sh
```

### 8-3. GitHub Actions 自動部署（選用）

機器上建一把專用金鑰，公鑰加進 `/home/ubuntu/.ssh/authorized_keys`，私鑰放 GitHub repo → Settings → Secrets：

| Secret | 值 |
|--------|----|
| `VPS_HOST` | Lightsail 靜態 IP |
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
          username: ubuntu
          key: ${{ secrets.VPS_SSH_KEY }}
          script: sudo /srv/english-tutor/deploy/update.sh
```

若 02-4 的 SSH 防火牆有限制來源 IP，GitHub Actions 的 runner IP 會被擋；
要嘛改成 any，要嘛改用下面的「Actions build 映像、機器只 pull」做法。

### 8-4. 進階：Actions build 推 ECR，機器只 pull（選用）

在 2 GB 機器上 build 會吃 swap 與 burst capacity；流量大或 build 變慢時可改成：

1. ECR 建三個 private repository：`english-backend`、`english-mcp`、`english-frontend`（每 GB $0.10/月，三個映像約 $0.1–0.3）。
2. GitHub Actions 用 OIDC（不需放 AWS key 在 GitHub）assume 一個只能 push ECR 的 IAM role，build 後 push。
3. `docker-compose.prod.yml` 的 `build:` 改成 `image: <account>.dkr.ecr.us-west-2.amazonaws.com/english-backend:latest`。
4. 機器上 07-2 的 IAM user 加 `ecr:GetAuthorizationToken` 與 `ecr:BatchGetImage` 等讀取權限，`update.sh` 改成 `aws ecr get-login-password | docker login` 再 `pull` + `up -d`。

這也是之後升級到方案 C（Fargate）的前置工作，映像已在 ECR，直接沿用。

### 8-5. 回滾

```bash
cd /srv/english-tutor
git log --oneline -5
git checkout <上一版 commit>
docker compose -f docker-compose.prod.yml up -d --build
```

資料表有變更時，先 `alembic downgrade -1` 再切版本；或直接用 07 的備份還原。
整台壞掉：Lightsail → Snapshots → 從快照 Create new instance，再把靜態 IP 換過去。

## 完成條件

- [ ] `update.sh` 一次跑完無錯誤
- [ ] 改一行前端文字 push 後，網站在 5 分鐘內更新（手動或 Actions）
- [ ] 練習過一次回滾

## 下一步

全部完成後回到 [總覽](00-README.md) 勾選完成條件。
之後若流量或功能成長，再看 [10-stage-b-fargate.md](10-stage-b-fargate.md)。

## 實作紀錄

（填寫日期、遇到的問題與解法）
