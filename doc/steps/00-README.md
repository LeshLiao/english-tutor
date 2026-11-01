# 實作步驟總覽

依《英文學習 MCP Server 本機架設規劃》的實作順序拆成獨立步驟，每個檔案一個目標。
請依編號順序進行，每一步結尾都有「完成條件」，全部打勾再進下一步。

| # | 檔案 | 目標 | 狀態 |
|---|------|------|------|
| 01 | [01-install-tools.md](01-install-tools.md) | 安裝 WSL2、Docker Desktop、Python、uv、Node.js | ⬜ |
| 02 | [02-docker-postgres.md](02-docker-postgres.md) | 建立專案骨架、docker-compose，跑起 PostgreSQL + Adminer | ⬜ |
| 03 | [03-fastapi-backend.md](03-fastapi-backend.md) | FastAPI 後端：models、Alembic migration、第一版 API | ⬜ |
| 04 | [04-mcp-server.md](04-mcp-server.md) | MCP Server（stdio）：`list_error_types`、`save_sentence`，註冊到 Claude Code | ⬜ |
| 05 | [05-claude-skill.md](05-claude-skill.md) | Claude Skill：手動檢查句子並儲存，跑通完整流程 | ⬜ |
| 06 | [06-claude-hook.md](06-claude-hook.md) | UserPromptSubmit Hook：自動偵測英文句子、背景分析 | ⬜ |
| 07 | [07-remaining-tools-and-api.md](07-remaining-tools-and-api.md) | 補齊其餘 MCP 工具與 API（stats、search、recent） | ⬜ |
| 08 | [08-react-frontend.md](08-react-frontend.md) | React 前端三個頁面：總覽、列表、詳情 | ⬜ |
| 09 | [09-mcp-http-mode.md](09-mcp-http-mode.md) | MCP Server 改 Streamable HTTP 跑在容器裡，為上雲做準備 | ⬜ |
| 10 | [10-aws-deploy.md](10-aws-deploy.md) | （未來）部署到 AWS | ⬜ |
| 10b | [../hostinger/00-README.md](../hostinger/00-README.md) | （未來）部署到 Hostinger VPS，階段 A 的替代方案 | ⬜ |

## 里程碑

- **M1（01–02）**：環境就緒，資料庫跑得起來。
- **M2（03–05）**：最小可用流程：Claude 手動檢查一句英文 → 存進資料庫。
- **M3（06–07）**：自動化：打字時自動偵測並儲存；所有查詢工具可用。
- **M4（08）**：網頁可看統計與複習。
- **M5（09–10）**：容器化 MCP，準備上雲。

## 使用方式

每完成一步，把上表的 ⬜ 改成 ✅，並在該步驟檔案最下方「實作紀錄」補上日期與遇到的問題。
