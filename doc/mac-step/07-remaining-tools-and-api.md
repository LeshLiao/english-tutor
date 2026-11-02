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

- [x] 五個 MCP 工具 + `dismiss_sentence` 都在 `/mcp` 列表中且可用（以 stdio client 列出 6 個工具並逐一呼叫，見實作紀錄）
- [x] 統計正確排除已 dismiss 的句子（pytest `test_dismiss_excludes_from_list_and_stats` + stdio 實測）
- [x] pytest 全綠（9 passed）
- [x] 三個 Skill 都可用（plugin 1.1.0，`claude -p` 新程序實測）

## 下一步

→ [08-react-frontend.md](08-react-frontend.md)

## 實作紀錄

### 2026-11-02（Claude Code 協助）

**完成內容**
- backend：`GET /sentences` 補 `q`（ILIKE 比對原句與修正句，不分大小寫）；新增 `PATCH /sentences/{id}`（body `{"is_dismissed": bool}`，可標記與取消）；新增 `GET /stats/trend?interval=day|week&from&to`，用 `date_trunc` 分組回傳 `period`、`sentence_count`、`error_count`，排除已 dismiss。`GET /sentences/{id}` 與 `GET /stats/errors` 在 03 就已存在。
- tests：新增關鍵字搜尋、dismiss 排除列表與統計（含取消、404、422）、trend 按日/週分組三個測試；`docker compose exec backend pytest` 9 passed。
- mcp-server：新增 `get_error_stats(from_date?, to_date?)`、`search_sentences(error_type?, keyword?, limit, include_dismissed)`、`get_recent_mistakes(limit)`（後端沒有「只要有錯」的篩選，多抓 3 倍再本地過濾）、`dismiss_sentence(sentence_id, dismissed=True)`；回傳統一經 `_summarize` 精簡成 Claude 好讀的形狀。server instructions 補上各工具的使用時機。
- Skill（lesh-marketplace `english-tutor-plugin` 1.0.0 → 1.1.0，已 push 並 `claude plugin update`）：`english-check` 第 1 步改為同時呼叫 `list_error_types` 與 `get_recent_mistakes`，第 5 步對重複的錯誤類型加註「（最近第 N 次犯 X 錯誤）」；新增 `english-stats [期間]`（表格 + 前三名各附一個最近例子 + 一句建議）與 `english-review [error_type] [count]`（兩回合：先只給原句讓使用者重寫，再對照儲存的修正句評分）。

**實測**
- stdio client 列出工具：`list_error_types, save_sentence, get_error_stats, search_sentences, get_recent_mistakes, dismiss_sentence`。`dismiss_sentence(26)` 後統計變動，`dismissed=False` 還原；id 999999 回 404 轉成 ToolError。
- `claude -p "/english-tutor-plugin:english-stats"` → 表格 6 種類型共 15 次，word choice 5 次居首。
- `claude -p "/english-tutor-plugin:english-review 2"` → 只列出 id 17、20 的原句，沒有洩漏修正。
- `claude -p "/english-tutor-plugin:english-check She go to school everyday."` → 存成 id 37，兩個錯誤分別標示「最近第 5 次犯 subject-verb agreement」「最近第 6 次犯 word choice」。

**限制 / 待確認**
- 新 MCP 工具在目前的 Claude Code session 看不到（stdio server 在 session 啟動時載入），重開後才會出現在 `/mcp`。
- `get_recent_mistakes` 的「最近第 N 次」是以回傳的前 10 句計算，不是嚴格的時間窗。
- 測試 hook 時又存了一筆重複的「I goes to school everyday.」（id 27），可用 `dismiss_sentence(27)` 排除。
