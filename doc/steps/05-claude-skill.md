# 05. Claude Skill：手動檢查句子

## 目標

寫一個 Skill，讓使用者可以用 `/english-check <句子>` 請 Claude 檢查英文、分類錯誤、透過 MCP 儲存。這是第一個**端到端**跑通的流程（M2 里程碑）。

## 前置條件

- [04](04-mcp-server.md) 完成，兩個 MCP 工具可用。

## 步驟

### 5-1. 建立 Skill 檔案

放在專案 `.claude/skills/english-check/SKILL.md`（專案層級，進 git），
同時在 `claude/skills/` 留一份原始檔方便管理（或用符號連結）。

### 5-2. SKILL.md 內容要點

frontmatter：

```yaml
---
name: english-check
description: Check an English sentence for grammar errors, explain the fix, classify each error, and save it via the english-practice MCP server. Invoke with /english-check <sentence>.
---
```

指令本體要告訴 Claude 依序做：

1. **先呼叫 `list_error_types`**，拿到現有分類。
2. 檢查句子，列出每個錯誤：出錯片段、建議改法、錯誤類型。
   - 類型**優先沿用**現有分類；確實沒有合適的才用新名稱，且名稱用小寫、簡短、單數（如 `article`、`preposition`、`word order`）。
3. 若句子完全正確，仍可呼叫 `save_sentence`（errors 為空）或直接回覆「正確」，二選一並在 Skill 裡明確規定。
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

- `/english-check I have went to Taipei last week.`
- `/english-check He is interesting in music.`
- `/english-check The weather is nice today.`（正確句）

確認：

- Claude 真的先呼叫 `list_error_types` 再呼叫 `save_sentence`。
- 第二句的 `interesting → interested` 類型若第一次叫 `word choice`，第三次類似錯誤應沿用同名，不會冒出 `vocabulary` 之類的同義新類型。
- Adminer 裡 `sentences`、`sentence_errors`、`error_types` 資料正確。

### 5-4. 調整

若分類不穩定，在 SKILL.md 補一份「建議類型清單」當起點，並在資料庫 seed 幾個常見類型（tense、article、preposition、subject-verb agreement、word order、word choice、plural、spelling）。

## 完成條件

- [ ] `/english-check` 可用，Claude 依 Skill 的步驟執行
- [ ] 連續多句測試後，`error_types` 沒有明顯同義重複
- [ ] 正確句的處理方式已定義並測過

## 下一步

→ [06-claude-hook.md](06-claude-hook.md)

## 實作紀錄

