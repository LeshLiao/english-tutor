# 07. 補齊其餘 MCP 工具與 API

## 目標

完成規劃中剩下的三個 MCP 工具與對應 API，並加上誤判回饋（dismiss）。完成後 Claude 能在使用者寫英文時主動提醒常犯錯誤。

## 前置條件

- [06](06-claude-hook.md) 完成。

## 步驟

### 7-1. API 補齊（backend）

| Method | Path | 說明 |
|--------|------|------|
| GET | `/sentences` | 支援 `error_type`、`q`（關鍵字）、`from`、`to`、`limit`、`offset`、`include_dismissed` |
| GET | `/sentences/{id}` | 詳情 |
| GET | `/stats/errors` | 依 `error_type_id` 分組計數，支援 `from`、`to`；排除 `is_dismissed` |
| GET | `/stats/trend` | 依日/週分組的錯誤數，給前端趨勢圖用 |
| PATCH | `/sentences/{id}` | 更新 `is_dismissed` |

### 7-2. MCP 工具補齊（mcp-server）

| 工具 | 對應 API | 說明 |
|------|----------|------|
| `get_error_stats(from?, to?)` | `GET /stats/errors` | 各錯誤類型次數 |
| `search_sentences(error_type?, keyword?, limit?)` | `GET /sentences` | 查過去句子複習 |
| `get_recent_mistakes(limit=10)` | `GET /sentences?limit=` | 最近錯誤，給 Claude 提醒用 |
| `dismiss_sentence(id)` | `PATCH /sentences/{id}` | 標記誤判 |

### 7-3. Skill 擴充

三個 Skill 都放在 `lesh-marketplace/plugins/english-tutor-plugin/skills/`，改完要 bump plugin 版本、push、`claude plugin update`。

- 在 `english-check` Skill 開頭加一步：先呼叫 `get_recent_mistakes`，若這次句子犯了最近同類錯誤，回覆時特別標示「這是你最近第 N 次犯 tense 錯誤」。
- 新增 Skill `english-stats`：呼叫 `get_error_stats` 並用表格摘要。
- 新增 Skill `english-review`：呼叫 `search_sentences` 抽幾句舊錯誤，讓使用者重寫一次。

### 7-4. 測試

- pytest 補齊所有新 endpoint，特別是 `is_dismissed` 被排除在統計外：

```bash
docker compose exec backend pytest -v
```

- 在 Claude Code 測：
  - 「我最近最常犯什麼錯？」→ Claude 呼叫 `get_error_stats`。
  - 「找出我犯過 preposition 錯誤的句子」→ `search_sentences`。
  - 「第 12 筆是誤判，忽略它」→ `dismiss_sentence`，之後統計數字減一。

## 完成條件

- [ ] 五個 MCP 工具 + `dismiss_sentence` 都在 `/mcp` 列表中且可用
- [ ] 統計正確排除已 dismiss 的句子
- [ ] pytest 全綠
- [ ] 三個 Skill 都可用

## 下一步

→ [08-react-frontend.md](08-react-frontend.md)

## 實作紀錄

