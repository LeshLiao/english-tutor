# 英文學習 MCP Server 規劃

## 目標

建立一套英文練習系統：在使用 Claude Code 時自動檢查英文句子，糾正錯誤並給出建議，把練習紀錄存進資料庫，再透過網頁查看統計與複習。

## 整體架構

| 元件 | 技術 | 說明 |
|------|------|------|
| Claude Skill | Claude Code Skill | 手動請 Claude 檢查句子是否正確，並呼叫 MCP 儲存 |
| Claude Code Hook | `UserPromptSubmit` hook | 每次送出 prompt 時自動偵測英文句子，於背景以 `claude -p`（無頭模式）啟動另一個 agent 分析句子，有錯誤時透過 MCP 儲存 |
| MCP Server | Python + FastMCP | 提供工具；建議透過 FastAPI 寫入資料，而非直接連資料庫 |
| 後端 | FastAPI | 提供 REST API，是所有資料讀寫的唯一入口 |
| 前端 | React | 網頁介面 |
| 資料庫 | PostgreSQL | 儲存練習紀錄 |
| 部署 | Docker Compose | 包含 Postgres、FastAPI、React（以及 MCP Server） |

**分工原則：** 句子的分析、糾正與錯誤分類交給 Claude；MCP Server 與後端只負責儲存與查詢。

## 資料表設計

### users

| 欄位 | 說明 |
|------|------|
| id | 主鍵 |
| name | 使用者名稱 |
| api_key | 用於 MCP 與 API 認證 |
| created_at | 建立時間 |

### sentences

| 欄位 | 說明 |
|------|------|
| id | 主鍵 |
| user_id | 對應 users，多人使用時區分資料 |
| original_text | 原句 |
| corrected_text | 修正後的句子 |
| explanation | 解釋說明 |
| source | 來源（hook 或 skill） |
| created_at | 建立時間 |

### error_types

| 欄位 | 說明 |
|------|------|
| id | 主鍵 |
| name | 錯誤類型名稱（如時態、冠詞、介係詞、語序） |
| description | 說明 |
| created_at | 建立時間 |

### sentence_errors

| 欄位 | 說明 |
|------|------|
| id | 主鍵 |
| sentence_id | 對應 sentences |
| error_type_id | 對應 error_types |
| error_snippet | 出錯的片段 |
| suggestion | 建議的改法 |

一個句子可能同時有多種錯誤，因此用 `sentence_errors` 做多對多關聯。統計某種錯誤的次數，只需對 `sentence_errors` 依 `error_type_id` 分組計數。

### 錯誤分類方式

由 Claude 自行分類，但為避免同義類型重複（例如 "tense" 與 "verb tense"），分類前先呼叫 `list_error_types` 取得現有類型，盡量沿用，確實沒有合適的才新增。

## MCP 工具

| # | 工具 | 說明 |
|---|------|------|
| 1 | `list_error_types` | 列出現有錯誤類型，供 Claude 分類時沿用 |
| 2 | `save_sentence` | 儲存一筆練習（原句、修正句、說明、各項錯誤），遇到新錯誤類型時一併新增 |
| 3 | `get_error_stats` | 統計各錯誤類型的次數，可依時間範圍篩選 |
| 4 | `search_sentences` | 依錯誤類型或關鍵字查詢過去的句子，方便複習 |
| 5 | `get_recent_mistakes` | 取得最近的錯誤，讓 Claude 在使用者寫英文時提醒常犯問題 |

**優先順序：** 先完成 `list_error_types` 與 `save_sentence` 打通流程，其餘逐步加入。

## 網頁規劃（React）

1. **總覽頁**：各錯誤類型次數圖表，以及隨時間變化的趨勢。
2. **句子列表頁**：可依錯誤類型、日期篩選。
3. **句子詳情頁**：原句與修正句並排比較，附上說明與各項錯誤。

## 其他注意事項

- **MCP 透過 FastAPI 寫入**：所有寫入走同一個入口，避免邏輯重複。
- **資料庫遷移**：使用 Alembic 管理資料表變更。
- **資料備份**：Postgres 掛載 Docker volume，避免容器刪除後資料遺失。
- **Hook 過濾**：過濾掉程式碼與中文，只送出真正的英文句子；避免把密鑰等敏感內容存入資料庫。
- **Hook 背景執行**：`claude -p` 需在背景執行，避免拖慢主對話。
- **複習功能（未來）**：加入錯題重練，把常犯的句型拿出來練習。

## AWS 部署規劃

全部元件都放到雲端，Claude Code 透過網址連線 MCP Server。

| 元件 | AWS 服務 | 說明 |
|------|----------|------|
| PostgreSQL | RDS for PostgreSQL | 放私有子網，只允許 ECS 連線；自動備份與升級 |
| FastAPI | ECR + ECS Fargate | Docker 映像檔推到 ECR，Fargate 執行，不需管理伺服器 |
| MCP Server | ECR + ECS Fargate | 改用 Streamable HTTP 傳輸（非 stdio），需加認證（API key 或 OAuth） |
| React | S3 + CloudFront | build 出靜態檔放 S3，CloudFront 提供 CDN 與 HTTPS |
| 對外入口 | Application Load Balancer | 處理 HTTPS，轉發到 FastAPI 與 MCP Server |
| 密鑰 | Secrets Manager | 資料庫密碼、API key 不寫在映像檔裡 |

**起步建議：** 先開一台 EC2 用 Docker Compose 跑整套，穩定後再拆成上表架構。

## Kubernetes 部署規劃

在 AWS 上使用 EKS；本機開發可用 kind 或 minikube 先驗證。

| 元件 | Kubernetes 資源 | 說明 |
|------|-----------------|------|
| FastAPI | Deployment + Service (ClusterIP) | 2 個以上副本，加 liveness/readiness probe |
| MCP Server | Deployment + Service (ClusterIP) | Streamable HTTP；需 session 黏著或無狀態設計 |
| React | Deployment (nginx) + Service，或仍放 S3 + CloudFront | 靜態檔用 nginx 容器提供 |
| PostgreSQL | 建議仍用 RDS；叢集內則用 StatefulSet + PVC | 資料庫放叢集內要自行處理備份與升級 |
| 對外入口 | Ingress (AWS Load Balancer Controller) | 一個網域、依路徑轉發：`/api`、`/mcp`、`/` |
| 設定與密鑰 | ConfigMap + Secret | 資料庫連線字串、API key；可搭配 External Secrets 接 Secrets Manager |
| 資料庫遷移 | Job | 部署前執行 Alembic migration |
| 打包 | Helm chart 或 Kustomize | 把所有 YAML 整理成一份可重複部署的設定 |

**注意事項：**

- Ingress 需搭配 cert-manager 或 ACM 取得 HTTPS 憑證。
- 用 HorizontalPodAutoscaler 依 CPU 自動擴縮 FastAPI。
- CI/CD：GitHub Actions build 映像檔推到 ECR，再 `kubectl apply` 或 `helm upgrade`。
- 小型個人專案 EKS 固定成本較高（控制平面每月約 $73），若只是練習可先用 ECS Fargate 或單台 EC2。

## 每月費用估算

以個人小流量、美東區域、全天運行粗估，數字為約略值（美元）。

| 方案 | 主要費用 | 每月合計（約） |
|------|----------|----------------|
| 單台 EC2 + Docker Compose | t3.small $15–20，全部元件跑在同一台 | $15–20 |
| ECS Fargate | RDS 最小規格 $15–20、Fargate 兩個小容器 $20–30、ALB $20、S3 + CloudFront 近乎免費 | $60–80 |
| EKS（完整架構） | 上列 ECS 費用 + EKS 控制平面 $73 + 至少一台 EC2 節點 $30 | $150–200 |

**備註：**

- 新帳號第一年有免費方案，RDS 與 EC2 部分可能免費。
- 費用隨流量、資料量與區域變動，上線前以 AWS Pricing Calculator 再確認。
- 個人練習建議由 EC2 或 ECS 起步，確定需要 Kubernetes 再升級到 EKS。

## 待釐清與補強事項

- **多人使用**：系統支援多位使用者，`sentences` 帶 `user_id`，所有 MCP 工具與 API 皆依 `user_id` 過濾；認證用每位使用者各自的 `api_key`。
- **Hook 誤判**：Claude 可能把技術術語或程式變數當成英文錯誤，需加「這不是錯誤」的回饋機制（例如 `sentences` 加 `is_dismissed` 欄位），避免污染統計。
- **測試**：MCP 工具與 FastAPI 需有自動化測試，特別是錯誤類型沿用與新增的邏輯。
- **監控與日誌**：上雲後需確認 hook 是否真的送出資料，至少接 CloudWatch Logs。
- **成本控制**：設定 AWS Budgets 警報，避免忘記關閉服務產生費用。
