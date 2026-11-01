# 05. Claude Code 連線與回歸測試

## 目標

本機 Claude Code 改連雲端 MCP，Skill 與 Hook 全部照常運作，資料寫進 VPS 的資料庫。

## 前置條件

- [04](04-domain-caddy-https.md) 完成，`https://<domain>/mcp` 帶 key 可連。

## 步驟

### 5-1. 切換 MCP 連線

```powershell
claude mcp remove english-practice
claude mcp add --transport http english-practice https://english.example.com/mcp --header "X-API-Key: <API_KEY>"
claude mcp list
```

在 Claude Code 裡打 `/mcp`，應顯示 `english-practice: connected`，工具清單與本機版相同。

> key 會寫進 `~/.claude.json`。若要共用設定檔給其他機器又不想明文，可改成 `--header "X-API-Key: ${ENGLISH_API_KEY}"` 並在系統環境變數設定。

### 5-2. 回歸測試

| 測試 | 預期 |
|------|------|
| `/english-check I goed to school yesterday.` | 回報錯誤並儲存；VPS 上 `psql` 查 `sentences` 多一筆 |
| 一般對話打一句英文（觸發 Hook） | 背景 `claude -p` 完成後資料庫多一筆，`source=hook` |
| `list_error_types`、`stats`、`search`、`recent` 工具 | 回傳與前端一致 |
| 故意把 header 改成錯的 key 再 `claude mcp add` | `/mcp` 顯示連線失敗 |
| VPS 上 `docker compose -f docker-compose.prod.yml restart mcp` | Claude Code 重連後正常 |

VPS 端查資料：

```bash
docker compose -f docker-compose.prod.yml exec db psql -U english -d english_practice -c "select id, source, created_at from sentences order by id desc limit 5;"
```

### 5-3. 延遲觀察

馬來西亞機房到台灣約 50–80 ms，Hook 在背景執行所以感覺不到；
`/english-check` 若明顯變慢，先看 `docker stats` 是否 CPU 吃滿（1 vCPU 在 build 時會），平時應在 5% 以下。

### 5-4. 本機版保留

本機 `docker compose up` 的開發環境照舊，只是 Claude Code 預設連雲端。
要切回本機測試新工具時：

```powershell
claude mcp remove english-practice
claude mcp add --transport http english-practice http://localhost:8001/mcp --header "X-API-Key: dev-local-key"
```

或在專案的 `.mcp.json` 用專案層級設定區分。

## 完成條件

- [ ] `/mcp` 顯示 connected，工具可用
- [ ] Skill 與 Hook 存進雲端資料庫
- [ ] 錯誤 key 被拒
- [ ] 換一個網路（手機熱點）仍可連

## 下一步

→ [06-backup-monitor.md](06-backup-monitor.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）
