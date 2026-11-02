# 05. Claude Skill：手動檢查句子

## 目標

寫一個 Skill，讓使用者可以用 `/english-check <句子>` 請 Claude 檢查英文、分類錯誤、透過 MCP 儲存。這是第一個**端到端**跑通的流程（M2 里程碑）。

## 前置條件

- [04](04-mcp-server.md) 完成，兩個 MCP 工具可用。

## 步驟

### 5-1. 建立 Skill 檔案

Skill **不放在本 repo**，而是放在個人 marketplace 的獨立 plugin：

```
~/sourceCode/marketplace/lesh-marketplace/plugins/english-tutor-plugin/skills/english-check/SKILL.md
```

安裝方式：

```bash
claude plugin marketplace update lesh-marketplace
claude plugin install english-tutor-plugin@lesh-marketplace
```

重開 Claude Code 後指令是 `/english-tutor-plugin:english-check <句子>`。

> 2026-11-02 原本放在專案 `.claude/skills/`（符號連結到 `claude/skills/`），當天改移到 marketplace。理由：之後 `english-stats`、`english-review` 也要放一起，而且 plugin 可以在多台機器安裝，不用每個 clone 各帶一份。MCP server 仍留在本 repo 並以 local scope 註冊，因為 stdio 指令含機器路徑。

> macOS 的 `ln -s` 支援相對路徑符號連結，git 也能正確追蹤；Windows 版需要額外權限，所以兩邊的做法不同。

### 5-2. SKILL.md 內容要點

frontmatter：

```yaml
---
name: english-check
version: 1.0.0
description: Check an English sentence for grammar errors, explain the fix, classify each error, and save it via the english-practice MCP server. Invoke with /english-check <sentence>.
argument-hint: <English sentence to check>
allowed-tools:
  - mcp__english-practice__list_error_types
  - mcp__english-practice__save_sentence
---
```

`allowed-tools` 列出兩個 MCP 工具，執行 Skill 時就不會每次跳權限詢問。

指令本體要告訴 Claude 依序做：

1. **先呼叫 `list_error_types`**，拿到現有分類。
2. 檢查句子，列出每個錯誤：出錯片段、建議改法、錯誤類型。
   - 類型**優先沿用**現有分類；確實沒有合適的才用新名稱，且名稱用小寫、簡短、單數（如 `article`、`preposition`、`word order`）。
3. 句子完全正確時**仍然呼叫 `save_sentence`，errors 為空陣列**（已決定採此做法，寫進 SKILL.md），這樣之後才能統計「寫對的比例」。
4. 呼叫 `save_sentence`，`source` 填 `skill`。
5. 回覆格式固定：

```
原句：...
修正：...
說明：...
錯誤：
- [tense] go → went
```

### 5-3. 測試

在 Claude Code 輸入幾句：

- `/english-tutor-plugin:english-check I have went to Taipei last week.`
- `/english-tutor-plugin:english-check He is interesting in music.`
- `/english-tutor-plugin:english-check The weather is nice today.`（正確句）

確認：

- Claude 真的先呼叫 `list_error_types` 再呼叫 `save_sentence`。
- 第二句的 `interesting → interested` 類型若第一次叫 `word choice`，第三次類似錯誤應沿用同名，不會冒出 `vocabulary` 之類的同義新類型。
- Adminer 裡 `sentences`、`sentence_errors`、`error_types` 資料正確。

### 5-4. 調整

若分類不穩定，在 SKILL.md 補一份「建議類型清單」當起點，並在資料庫 seed 幾個常見類型（tense、article、preposition、subject-verb agreement、word order、word choice、plural、spelling）。

## 完成條件

- [x] `/english-tutor-plugin:english-check` 可用，Claude 依 Skill 的步驟執行（plugin 1.0.0 安裝後以 `claude -p` 新程序實測，見實作紀錄）
- [x] 連續多句測試後，`error_types` 沒有明顯同義重複（四個類型：plural、subject-verb agreement、tense、word choice）
- [x] 正確句的處理方式已定義並測過（存入 id 22，errors 為空）

## 下一步

→ [06-claude-hook.md](06-claude-hook.md)

## 實作紀錄

### 2026-11-02（Claude Code 協助）

**完成內容**
- `claude/skills/english-check/SKILL.md`，`.claude/skills/english-check` 為指向它的符號連結。**同日稍後移到 marketplace 的 `english-tutor-plugin` 1.0.0**，本 repo 內兩個目錄已刪除。
- SKILL.md 內容：四個步驟（先 `list_error_types` → 分類 → `save_sentence` → 固定格式回覆）、類型命名規則與 15 個建議起始名稱、正確句也存（errors 空）、四種邊界情況（空參數、非英文、多句、後端錯誤）。
- 三句測試結果：
  - `I have went to Taipei last week.` → id 20，`tense`（沿用既有）
  - `He is interesting in music.` → id 21，`word choice`（沿用既有，沒有冒出 `vocabulary`）
  - `The weather is nice today.` → id 22，errors 為空
- 測試後 `error_types` 仍只有四個類型，無同義重複。沒有 seed 資料庫，靠 SKILL.md 的建議清單就夠穩。

**限制**
- Skill 清單在 Claude Code 啟動時載入，本 session 看不到新 Skill，所以是依 SKILL.md 的步驟手動呼叫 MCP 工具驗證。請重開 Claude Code 後實際輸入 `/english-check <句子>` 確認一次。

### 2026-11-02（plugin 安裝後實測）

- `claude plugin marketplace update` → `claude plugin install english-tutor-plugin@lesh-marketplace` 成功，快取在 `~/.claude/plugins/cache/lesh-marketplace/english-tutor-plugin/1.0.0/`，內容與 marketplace 來源一致。
- 既有的 Claude Code session 看不到新 skill（`Unknown skill`），改用新程序測：

```bash
env -u CLAUDECODE claude -p "/english-tutor-plugin:english-check I goes to school everyday." \
  --allowedTools "mcp__english-practice__list_error_types,mcp__english-practice__save_sentence"
```

- 結果：固定格式回覆、兩個錯誤 `subject-verb agreement`（goes → go）與 `word choice`（everyday → every day）都沿用既有類型、存入 id 23、`error_types` 仍只有四個。
- `env -u CLAUDECODE` 是因為在 Claude Code 裡面再開 `claude -p` 會被巢狀檢查擋下；步驟 06 的 hook 也要這樣處理。

**里程碑 M2 達成**：Claude 手動檢查一句英文 → 存進資料庫的完整流程可用。

