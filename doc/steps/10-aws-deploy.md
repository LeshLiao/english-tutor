# 10. AWS 部署（未來）

## 目標

把整套系統搬上 AWS，Claude Code 透過公開網址連線 MCP Server。細節依《英文學習 MCP Server 規劃》的 AWS 與 Kubernetes 章節。

## 前置條件

- [09](09-mcp-http-mode.md) 完成，本機容器版穩定運作至少一週。

> **詳細步驟：** AWS 版逐步文件見 [../aws/00-README.md](../aws/00-README.md)（2026-11-01 重新規劃，起步改用 Lightsail $12/月，含費用試算）。
> **替代方案：** 階段 A 也可以改用 Hostinger KVM VPS（更便宜、內建 Docker），步驟見 [../hostinger/00-README.md](../hostinger/00-README.md)。

## 建議路線

依規劃文件的「起步建議」分三階段，**不要一開始就上 EKS**。

### 階段 A：單台 EC2 + Docker Compose（約 $15–20/月）

1. 開一台 t3.small（Ubuntu），裝 Docker。
2. 把 repo clone 上去，`.env` 改成正式密碼，`docker compose --profile http --profile prod up -d`。
3. 設定 Security Group 只開 443（與 22 限自己 IP）。
4. 用 Caddy 或 nginx 加 Let's Encrypt HTTPS，反向代理 `/api`、`/mcp`、`/`。
5. 設 AWS Budgets 警報（例如 $30）。
6. Claude Code 改連 `https://<domain>/mcp`。

### 階段 B：ECS Fargate + RDS（約 $60–80/月）

- 映像推到 ECR；FastAPI 與 MCP 各一個 Fargate service。
- 資料庫改用 RDS PostgreSQL（私有子網）。
- 前端 build 放 S3 + CloudFront。
- ALB 處理 HTTPS 與路徑轉發。
- 密鑰改放 Secrets Manager。
- CloudWatch Logs 確認 hook 真的有寫入。

### 階段 C：EKS（只有確定需要 Kubernetes 時）

- Helm chart 或 Kustomize 打包。
- Alembic migration 用 Job 跑。
- HPA、Ingress + cert-manager / ACM。
- 控制平面固定成本 $73/月，個人練習不建議。

## 搬家時要改的東西

| 項目 | 本機 | AWS |
|------|------|-----|
| MCP 連線 | `http://localhost:8001/mcp` | `https://<domain>/mcp` |
| 密鑰 | `.env` | Secrets Manager |
| 資料庫 | compose `db` | RDS endpoint |
| 前端 API URL | `localhost:8000` | `https://<domain>/api` |

程式碼不變，只換環境變數與部署設定。

## 完成條件

- [ ] Claude Code 從任何網路都能連上 MCP
- [ ] HTTPS 正常，HTTP 自動轉 HTTPS
- [ ] Budgets 警報已設
- [ ] 資料庫有自動備份

## 實作紀錄

