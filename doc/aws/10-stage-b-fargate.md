# 10. 進階：ECS Fargate + RDS + ALB（方案 C）規劃

方案 A 跑穩之後，若出現下列任一情況才考慮升級；否則單機方案 A 可以一直用下去。

- 多人同時使用，單機 CPU 經常超過 50%。
- 需要零停機部署（單機 `up -d --build` 會斷線幾十秒）。
- 想把 AWS 正規架構（VPC、ECS、RDS、ALB、IAM role）練一遍。

每月約 $80，明細見 [09-cost.md](09-cost.md) 第四節。

## 架構

```
Route 53 ──▶ CloudFront ──▶ S3（React 靜態檔，OAC 私有存取）
     │
     └─────▶ ALB（ACM 憑證、HTTPS）
               ├── /api/*  ──▶ ECS Service: backend（Fargate 0.25 vCPU / 0.5 GB）
               └── /mcp*   ──▶ ECS Service: mcp    （Fargate 0.25 vCPU / 0.5 GB）
                                        │
                                  RDS PostgreSQL db.t4g.micro（private subnet，只允許 ECS SG）
Secrets Manager ──▶ ECS task 環境變數（DB 密碼、API key）
CloudWatch Logs ◀── 所有 task stdout
ECR ◀── GitHub Actions（OIDC）push 映像
```

| 元件 | AWS 服務 | 說明 |
|------|----------|------|
| PostgreSQL | RDS for PostgreSQL 16，db.t4g.micro，Single-AZ，gp3 20 GB | 自動備份 7 天；private subnet；Security Group 只收 ECS SG 的 5432 |
| FastAPI | ECS Fargate service，1 task | public subnet + 公開 IP（避免 NAT Gateway），SG 只收 ALB 的 8000 |
| MCP Server | ECS Fargate service，1 task | 同上，port 8001；Streamable HTTP 無狀態設計，之後要擴到 2 task 才不用 sticky session |
| React | S3 + CloudFront | `npm run build` 上傳 S3；CloudFront 用 OAC 讀 S3，不開 bucket 公開 |
| 入口 | ALB + ACM | 一個 listener 443，兩條 path rule；HTTP 80 轉 443 |
| 密鑰 | Secrets Manager | task definition 用 `secrets:` 引用，不寫在映像或環境變數明文 |
| 日誌 | CloudWatch Logs | `awslogs` driver，保留 30 天 |
| 映像 | ECR | 08-4 已建好的話直接沿用 |
| Migration | ECS one-off task 或 backend 啟動時 `alembic upgrade head` | 單 task 的情況下後者最簡單 |

Caddy 在這個架構裡消失：HTTPS 由 ALB + ACM 處理；basic auth 與 API key 注入改由 backend 自己做
（或 ALB 前面加 CloudFront + Lambda@Edge，個人用殺雞用牛刀）。

## 搬家步驟概要

1. **ECR + GitHub Actions**：照 [08-4](08-update-cicd.md) 把三個映像推上 ECR。
2. **VPC**：用預設 VPC 即可（2 個 public subnet）；RDS 另建 2 個 private subnet 與 DB subnet group。
3. **RDS**：建 db.t4g.micro，密碼交給 Secrets Manager 自動產生；從 07 的 S3 dump `pg_restore` 匯入資料（在一台臨時 Lightsail 或本機透過 SSH tunnel）。
4. **Secrets Manager**：建 `english/api-key`；DB 密碼由 RDS 建立時自動建。
5. **ECS**：建 cluster（Fargate）、兩個 task definition（`secrets:` 引用密鑰，`awslogs`）、兩個 service。
6. **ALB + ACM**：ACM 申請網域憑證（DNS 驗證，Route 53 一鍵）；ALB listener 443，target group 各指向兩個 service；health check `/health`。
7. **S3 + CloudFront**：bucket 放 build 產物；CloudFront distribution 以 OAC 讀 S3，alternate domain + ACM（**CloudFront 的憑證要申請在 us-east-1**）。
8. **Route 53**：`english.example.com` → CloudFront alias；`api.english.example.com` → ALB alias（或同網域用 CloudFront behavior 轉 `/api`、`/mcp` 到 ALB）。
9. **Claude Code**：`claude mcp add` 改指向新網址，回歸測試同 [06](06-claude-connect.md)。
10. **切換**：DNS TTL 先降到 60 秒，確認新環境資料一致後切換；Lightsail 保留一週再刪（記得刪靜態 IP）。

## 費用控制

- Budgets 金額改成 $100，警報門檻 80% / 100%。
- 每個 Fargate task 都是 0.25 vCPU / 0.5 GB（最小規格），不要用預設的 1 vCPU / 2 GB。
- 不要建 NAT Gateway；task 放 public subnet 開公開 IP。
- RDS 選 Single-AZ、關閉 Performance Insights 付費版、儲存自動擴展上限設 50 GB。
- 晚上不用可以把 ECS service desired count 設 0（用 EventBridge Scheduler），Fargate 以秒計費；RDS 也可以停 7 天（會自動重啟）。

## 替代：ECS on EC2 / EKS

- **ECS on EC2**：ALB + RDS 不變，Fargate 換成一台 t4g.small 當 container instance，每月省約 $10，但要自己顧機器，等於方案 A 加 ALB，不太划算。
- **EKS**：控制平面 $73/月 + 節點，每月 $160 以上；K8s 資源對應見 [英文學習 MCP Server 規劃](../英文學習%20MCP%20Server%20規劃.md) 的 Kubernetes 章節。只有想練 K8s 才做。

## 實作紀錄

（填寫日期、遇到的問題與解法）
