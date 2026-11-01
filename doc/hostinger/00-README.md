# Hostinger 部署總覽

把整套系統（PostgreSQL、FastAPI、MCP Server、React）部署到一台 Hostinger KVM VPS，
Claude Code 透過公開網址連線 MCP Server。這是 [steps/10-aws-deploy.md](../steps/10-aws-deploy.md)
「階段 A：單台機器 + Docker Compose」的 Hostinger 版本，程式碼完全不變，只換環境變數與部署設定。

## 為什麼選 Hostinger VPS

| 項目 | Hostinger KVM 1 | AWS t3.small（原規劃） |
|------|-----------------|------------------------|
| 規格 | 1 vCPU、4 GB RAM、50 GB NVMe、4 TB 流量 | 2 vCPU、2 GB RAM、磁碟另計 |
| 月費 | 促銷 $6.49（24 個月一次付清 $155.76）；續約 $11.99 | $15–20 |
| Docker | 選 Docker 範本即內建 docker-ce + docker compose | 自己裝 |
| 管理介面 | hPanel：防火牆、快照、Docker Manager、瀏覽器終端機 | Console / Security Group |
| 亞洲機房 | 馬來西亞、印尼、印度（**無新加坡、無台灣**） | 東京、新加坡等 |

- 共享主機（Web / Cloud 方案）**不能用**：官方明說不支援 PostgreSQL，也跑不了 FastAPI（ASGI）與長駐的 MCP Server。
- KVM 1 就夠：五個容器（db、backend、mcp、frontend、caddy）合計記憶體遠低於 2 GB。
- 價格數字為 2026-11-01 查到的美金價，購買前以 hostinger.com 當下頁面為準。

## 架構

```
Internet ──443──▶ Caddy（自動 Let's Encrypt）
                    ├── /api/*  ──▶ backend:8000  (FastAPI)
                    ├── /mcp*   ──▶ mcp:8001      (MCP Streamable HTTP)
                    └── /*      ──▶ frontend:80   (nginx + React build)
                                        │
                                     db:5432 (PostgreSQL，只在 Docker 內網)
```

只有 Caddy 對外開 80/443；db、backend、mcp、frontend 都不對外開 port。

## 步驟

| # | 檔案 | 目標 | 狀態 |
|---|------|------|------|
| 01 | [01-buy-vps.md](01-buy-vps.md) | 購買 KVM 1、選 Docker 範本與機房、設定 SSH 金鑰、首次登入 | ⬜ |
| 02 | [02-server-setup.md](02-server-setup.md) | 系統更新、防火牆、swap、clone repo、正式版 `.env` | ⬜ |
| 03 | [03-compose-prod.md](03-compose-prod.md) | 寫 `docker-compose.prod.yml`，在 VPS 上 build 並啟動全部服務 | ⬜ |
| 04 | [04-domain-caddy-https.md](04-domain-caddy-https.md) | 網域 DNS 指向 VPS、Caddyfile 反向代理、HTTPS 生效 | ⬜ |
| 05 | [05-claude-connect.md](05-claude-connect.md) | Claude Code 改連 `https://<domain>/mcp`，Skill 與 Hook 回歸測試 | ⬜ |
| 06 | [06-backup-monitor.md](06-backup-monitor.md) | 資料庫每日備份、Hostinger 快照、日誌與基本監控 | ⬜ |
| 07 | [07-update-cicd.md](07-update-cicd.md) | 更新流程；選用 GitHub Actions 自動部署 | ⬜ |

## 前置條件

- [steps/09-mcp-http-mode.md](../steps/09-mcp-http-mode.md) 完成，本機容器版（`--profile http --profile prod`）穩定跑過至少一週。
- 有一個網域（可在 Hostinger 或任何註冊商購買）。
- 本機有 SSH 用戶端（Windows 11 內建 `ssh`、`ssh-keygen`）。

## 完成條件（全部）

- [ ] Claude Code 從任何網路都能連上 `https://<domain>/mcp`
- [ ] `https://<domain>` 看得到前端，`http://` 自動轉 `https://`
- [ ] 錯誤 API key 連 `/mcp` 與 `/api` 都被拒絕
- [ ] 資料庫每日自動備份，且實際還原測試過一次
- [ ] 知道怎麼在 10 分鐘內更新一版

## 使用方式

與 `doc/steps` 相同：每完成一步，把上表 ⬜ 改成 ✅，並在該檔最下方「實作紀錄」補上日期與遇到的問題。
