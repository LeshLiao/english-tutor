# 實作步驟總覽（macOS 版）

依《英文學習 MCP Server 本機架設規劃》的實作順序拆成獨立步驟，每個檔案一個目標。
請依編號順序進行，每一步結尾都有「完成條件」，全部打勾再進下一步。

> 本目錄是 [../steps/](../steps/00-README.md)（Windows 版）的 macOS 對應版本。
> 專案內容、資料表、API、MCP 工具設計完全相同，只有**安裝方式、終端機指令、路徑、背景程序**等與作業系統相關的部分不同。
> 兩邊的步驟編號一一對應，可互相參照。

| # | 檔案 | 目標 | 狀態 |
|---|------|------|------|
| 01 | [01-install-tools.md](01-install-tools.md) | 安裝 Homebrew、Docker Desktop、uv（含 Python 3.12）、Node.js | ✅ |
| 02 | [02-docker-postgres.md](02-docker-postgres.md) | 建立專案骨架、docker-compose，跑起 PostgreSQL + Adminer | ✅ |
| 03 | [03-fastapi-backend.md](03-fastapi-backend.md) | FastAPI 後端：models、Alembic migration、第一版 API | ✅ |
| 04 | [04-mcp-server.md](04-mcp-server.md) | MCP Server（stdio）：`list_error_types`、`save_sentence`，註冊到 Claude Code | ✅ |
| 05 | [05-claude-skill.md](05-claude-skill.md) | Claude Skill：手動檢查句子並儲存，跑通完整流程（Skill 放在 lesh-marketplace 的 english-tutor-plugin） | ✅ |
| 06 | [06-claude-hook.md](06-claude-hook.md) | UserPromptSubmit Hook：自動偵測英文句子、背景分析 | ✅ |
| 07 | [07-remaining-tools-and-api.md](07-remaining-tools-and-api.md) | 補齊其餘 MCP 工具與 API（stats、search、recent） | ✅ |
| 08 | [08-react-frontend.md](08-react-frontend.md) | React 前端三個頁面：總覽、列表、詳情 | ✅ |
| 09 | [09-mcp-http-mode.md](09-mcp-http-mode.md) | MCP Server 改 Streamable HTTP 跑在容器裡，為上雲做準備 | ⬜ |
| 10 | [../aws/00-README.md](../aws/00-README.md) | （未來）部署到 AWS（Lightsail 起步，逐步文件與費用試算） | ⬜ |
| 10b | [../hostinger/00-README.md](../hostinger/00-README.md) | （未來）部署到 Hostinger VPS，階段 A 的替代方案 | ⬜ |

## 里程碑

- **M1（01–02）**：環境就緒，資料庫跑得起來。
- **M2（03–05）**：最小可用流程：Claude 手動檢查一句英文 → 存進資料庫。
- **M3（06–07）**：自動化：打字時自動偵測並儲存；所有查詢工具可用。
- **M4（08）**：網頁可看統計與複習。
- **M5（09–10）**：容器化 MCP，準備上雲。

## macOS 與 Windows 版的主要差異

| 項目 | Windows（`../steps/`） | macOS（本目錄） |
|------|------------------------|-----------------|
| 套件管理 | winget | Homebrew |
| 容器前置 | 需先裝 WSL2 | 不需要，Docker Desktop for Mac 直接可用 |
| 終端機 | PowerShell | zsh（內建 Terminal 或 iTerm2） |
| Python | winget 裝 3.12 | `uv python install 3.12`（不用 Homebrew 的 python3） |
| 專案路徑 | `C:\Users\dlnx3\sourceCode\english-tutor` | `/Users/lesh/sourceCode/english-tutor` |
| Hook 背景程序 | `DETACHED_PROCESS` | `start_new_session=True` |
| Docker 記憶體上限 | `.wslconfig` | Docker Desktop → Settings → Resources |

## 使用方式

每完成一步，把上表的 ⬜ 改成 ✅，並在該步驟檔案最下方「實作紀錄」補上日期與遇到的問題。
