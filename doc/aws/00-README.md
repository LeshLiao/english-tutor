# AWS 部署總覽

把整套系統（PostgreSQL、FastAPI、MCP Server、React）部署到 AWS，
Claude Code 透過公開網址連線 MCP Server。程式碼與本機版完全相同，只換環境變數與部署設定。

這份文件取代 [steps/10-aws-deploy.md](../steps/10-aws-deploy.md) 的粗略規劃，
並與 [hostinger/](../hostinger/00-README.md) 平行：兩邊都是「單台機器 + Docker Compose」，只是機器換成 AWS。

> 價格皆為 2026-11-01 上網查到的美金價（Oregon 區域，us-west-2），細節與來源見 [09-cost.md](09-cost.md)。
> 開始前請再到 AWS 價格頁或 Pricing Calculator 確認一次。

## 三種方案比較

| 方案 | 架構 | 每月約 | 適合 |
|------|------|--------|------|
| **A. Lightsail（推薦起步）** | 一台 Lightsail $12 VPS（2 vCPU / 2 GB / 60 GB / 3 TB 流量，含 IPv4）跑 Docker Compose | **$13** | 個人使用、先跑起來 |
| A'. EC2 | 一台 t4g.small + EBS + 公開 IPv4，其餘同 A | $19 | 之後要接 VPC 內其他服務，或想用台北區域（Lightsail 沒有台北） |
| B. Lightsail + 託管資料庫 | A 的 VPS + Lightsail Managed PostgreSQL（$15） | $28 | 想要資料庫自動備份、不想自己顧 Postgres |
| C. ECS Fargate + RDS + ALB | 正統無伺服器容器架構，見 [10-stage-b-fargate.md](10-stage-b-fargate.md) | $60–75 | 多人使用、要高可用、想練 AWS 正規架構 |
| D. EKS | C 再加 EKS 控制平面 $73 + 節點 | $150 以上 | 練 Kubernetes 才需要，個人專案不建議 |

**結論：先做 A。** 程式碼不變，之後要升級到 B 或 C 只換部署設定。

## 為什麼是 Lightsail 而不是 EC2

| 項目 | Lightsail $12 | EC2 t4g.small（Oregon） |
|------|---------------|------------------------|
| 規格 | 2 vCPU、2 GB、60 GB SSD、3 TB 流量 | 2 vCPU（ARM）、2 GB，磁碟與流量另計 |
| 月費 | $12 固定，含公開 IPv4 與流量 | 約 $12.3 + EBS 30 GB $2.4 + IPv4 $3.65 ≈ $19 |
| 設定 | 網頁精靈 5 分鐘，防火牆、快照、監控警報都在同一頁 | 要自己設 VPC、Security Group、EIP、CloudWatch |
| 區域 | Oregon、東京、新加坡等，**無台北** | 所有區域，含台北（ap-east-2） |
| CPU 架構 | x86_64，映像檔與本機相同 | ARM64，要在機器上 build 或多架構 build |

Lightsail 就是包裝過的 EC2，底層一樣，比較便宜又好上手。

## 架構（方案 A）

```
Internet ──443──▶ Lightsail 防火牆（只開 22/80/443）
                    │
                  Caddy（自動 Let's Encrypt）
                    ├── /api/*  ──▶ backend:8000  (FastAPI)
                    ├── /mcp*   ──▶ mcp:8001      (MCP Streamable HTTP)
                    └── /*      ──▶ frontend:80   (nginx + React build)
                                        │
                                     db:5432 (PostgreSQL，只在 Docker 內網)

每日 pg_dump ──▶ S3 bucket（30 天自動刪除）
Lightsail 自動快照（每日，保留 7 天）
Lightsail 警報 ──▶ Email
```

只有 Caddy 對外開 80/443；db、backend、mcp、frontend 都不對外開 port。

## 步驟

| # | 檔案 | 目標 | 狀態 |
|---|------|------|------|
| 01 | [01-account-region-budget.md](01-account-region-budget.md) | 帳號安全檢查、IAM 使用者、確認區域（Oregon）、設 Budgets 警報 | ⬜ |
| 02 | [02-lightsail-instance.md](02-lightsail-instance.md) | 在 Oregon 建立 Lightsail $12 實例、靜態 IP、防火牆、SSH 登入、裝 Docker | ✅ |
| 03 | [03-server-setup.md](03-server-setup.md) | 系統更新、swap、clone repo、正式版 `.env` | ✅ |
| 04 | [04-compose-prod.md](04-compose-prod.md) | `docker-compose.prod.yml` 在 Lightsail 上 build 並啟動 | ✅ |
| 05 | [05-domain-caddy-https.md](05-domain-caddy-https.md) | Route 53（或既有註冊商）DNS、Caddy 反向代理、HTTPS | ⬜ |
| 06 | [06-claude-connect.md](06-claude-connect.md) | Claude Code 改連 `https://<domain>/mcp`，回歸測試 | ⬜ |
| 07 | [07-backup-monitor.md](07-backup-monitor.md) | pg_dump 到 S3、Lightsail 自動快照、警報 | ⬜ |
| 08 | [08-update-cicd.md](08-update-cicd.md) | 更新流程；選用 GitHub Actions 自動部署 | ⬜ |
| 09 | [09-cost.md](09-cost.md) | 費用明細、各方案試算、查價來源 | 參考 |
| 10 | [10-stage-b-fargate.md](10-stage-b-fargate.md) | 之後升級到 ECS Fargate + RDS + ALB 的規劃 | 未來 |
| 紀錄 | [local-to-lightsail.md](local-to-lightsail.md) | 2026-11-02 從本機到 Lightsail 的實際部署過程（03 後半 + 04） | 參考 |

## 前置條件

- [steps/09-mcp-http-mode.md](../steps/09-mcp-http-mode.md) 完成，本機容器版（`--profile http --profile prod`）穩定跑過至少一週。
- 既有的 AWS 帳號，root 可登入。
- 一個網域（可在 Route 53 買，或用既有註冊商）。
- 本機為 macOS，終端機內建 `ssh`、`ssh-keygen`、`curl`、`dig`；AWS 操作全部用瀏覽器 Console。

## 完成條件（全部）

- [ ] Claude Code 從任何網路都能連上 `https://<domain>/mcp`
- [ ] `https://<domain>` 看得到前端，`http://` 自動轉 `https://`
- [ ] 錯誤 API key 連 `/mcp` 與 `/api` 都被拒絕
- [ ] 資料庫每日自動備份到 S3，且實際還原測試過一次
- [ ] AWS Budgets 警報已設，收過一次測試通知
- [ ] 知道怎麼在 10 分鐘內更新一版

## 使用方式

與 `doc/steps` 相同：每完成一步，把上表 ⬜ 改成 ✅，並在該檔最下方「實作紀錄」補上日期與遇到的問題。
