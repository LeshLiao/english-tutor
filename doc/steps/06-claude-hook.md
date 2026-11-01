# 06. Claude Code Hook：自動偵測英文

## 目標

加上 `UserPromptSubmit` hook，每次送出 prompt 時自動判斷是否含英文句子，若是則在**背景**用 `claude -p` 啟動另一個 agent 分析並透過 MCP 儲存，主對話完全不受影響。

## 前置條件

- [05](05-claude-skill.md) 完成，手動流程已穩定。

## 步驟

### 6-1. 建立 hook script

`claude/hooks/check_english.py`，職責：

1. 從 stdin 讀 JSON（Claude Code 會傳入 `prompt` 等欄位）。
2. **過濾**，以下情況直接結束、不處理：
   - 含中文字元。
   - 含程式碼特徵（反引號、`{}`、`;`、`=>`、`def `、`import ` 等）。
   - 含疑似密鑰（`sk-`、`AKIA`、`password=`、長串隨機字元）。
   - 字數太短（< 4 個字）或太長（> 300 字）。
   - 以 `/` 開頭（slash command，避免 `/english-check` 被重複處理）。
3. 通過過濾才用 `subprocess.Popen` 在背景啟動：

```
claude -p "<檢查指令，內容同 Skill 的步驟，source 填 hook>" --allowedTools "mcp__english-practice__*"
```

   - 用 `creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP`（Windows）讓它脫離父程序。
   - stdout / stderr 導到 log 檔（例如 `claude/hooks/logs/`），方便除錯。
4. 立刻 `print("")` 並 `exit 0`，不等待結果。

### 6-2. 註冊 hook

專案 `.claude/settings.json`：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python C:\\Users\\dlnx3\\sourceCode\\english-tutor\\claude\\hooks\\check_english.py"
          }
        ]
      }
    ]
  }
}
```

> 這份設定放專案層級代表只有在這個 repo 裡才觸發。若想在所有專案都練習英文，改放 `~/.claude/settings.json`。

### 6-3. 避免遞迴

背景的 `claude -p` 本身也會觸發 `UserPromptSubmit` hook。在 script 裡加環境變數標記（例如啟動子程序時設 `ENGLISH_HOOK_CHILD=1`），script 開頭檢查到就直接結束。

### 6-4. 測試

1. 先手動測過濾邏輯：

```powershell
echo '{"prompt":"I goes to school everyday."}' | python claude/hooks/check_english.py
echo '{"prompt":"請幫我看一下"}' | python claude/hooks/check_english.py
echo '{"prompt":"const x = 1;"}' | python claude/hooks/check_english.py
```

   只有第一句應該啟動子程序（看 log 檔）。

2. 在 Claude Code 隨意打一句有錯的英文，幾秒後到 Adminer 確認 `sentences` 多一筆，`source = hook`。
3. 確認主對話沒有變慢。
4. 打一句技術描述（如 "refactor the useEffect hook"），看是否被誤判；若有，記下來，這是 `is_dismissed` 的用途。

## 完成條件

- [ ] 過濾邏輯三種測試結果正確
- [ ] 打英文 prompt 後幾秒內資料庫自動多一筆 `source = hook`
- [ ] 中文、程式碼、slash command 不會觸發
- [ ] 不會無限遞迴（log 裡只有一層）
- [ ] 主對話回應速度沒有明顯變慢

## 下一步

→ [07-remaining-tools-and-api.md](07-remaining-tools-and-api.md)

## 實作紀錄

