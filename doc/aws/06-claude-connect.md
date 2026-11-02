# 06. Claude Code 連線與回歸測試

## 目標

本機 Claude Code 改連 AWS 上的 MCP，Skill 與 Hook 全部照常運作，資料寫進 Lightsail 上的資料庫。

## 前置條件

- [05](05-domain-caddy-https.md) 完成，`https://<domain>/mcp` 帶 key 可連。

## 步驟

步驟與 [hostinger/05-claude-connect.md](../hostinger/05-claude-connect.md) 完全相同，重點摘要：

### 6-1. 切換 MCP 連線

```bash
claude mcp remove english-practice
claude mcp add --transport http english-practice https://english.example.com/mcp --header "X-API-Key: <API_KEY>"
claude mcp list
```

在 Claude Code 裡打 `/mcp`，應顯示 `english-practice: connected`，工具清單與本機版相同。

### 6-2. 回歸測試

| 測試 | 預期 |
|------|------|
| `/english-check I goed to school yesterday.` | 回報錯誤並儲存；機器上 `psql` 查 `sentences` 多一筆 |
| 一般對話打一句英文（觸發 Hook） | 背景 `claude -p` 完成後資料庫多一筆，`source=hook` |
| `list_error_types`、`stats`、`search`、`recent` 工具 | 回傳與前端一致 |
| 故意把 header 改成錯的 key 再 `claude mcp add` | `/mcp` 顯示連線失敗 |
| 機器上 `docker compose -f docker-compose.prod.yml restart mcp` | Claude Code 重連後正常 |

機器端查資料：

```bash
docker compose -f docker-compose.prod.yml exec db psql -U english -d english_practice -c "select id, source, created_at from sentences order by id desc limit 5;"
```

### 6-3. 延遲觀察

Oregon 到台灣約 130–160 ms，Hook 在背景執行所以感覺不到；
手動 `/english-check` 一次工具呼叫來回幾趟，比本機多約 0.5–1 秒，屬正常；
`/english-check` 若明顯變慢，到 Lightsail 實例頁 Metrics 看 CPU 與 burst capacity，平時應在 5% 以下。

### 6-4. 本機版保留

本機 `docker compose up` 的開發環境照舊，只是 Claude Code 預設連雲端。
要切回本機測試新工具時：

```bash
claude mcp remove english-practice
claude mcp add --transport http english-practice http://localhost:8001/mcp --header "X-API-Key: dev-local-key"
```

## 完成條件

- [ ] `/mcp` 顯示 connected，工具可用
- [ ] Skill 與 Hook 存進雲端資料庫
- [ ] 錯誤 key 被拒
- [ ] 換一個網路（手機熱點）仍可連

## 下一步

→ [07-backup-monitor.md](07-backup-monitor.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）

### 2026-11-02（暫時版：先用 IP 走 HTTP，05 做完再換 https）

使用者決定不等網域，先讓 Claude Code 連雲端 MCP。

```bash
KEY=$(ssh english-tutor "grep '^API_KEY=' /srv/english-tutor/.env | cut -d= -f2")   # 不要 echo
claude mcp remove english-practice
claude mcp add --transport http english-practice http://44.228.11.180/mcp --header "X-API-Key: $KEY"
claude mcp list        # english-practice: http://44.228.11.180/mcp (HTTP) - ✔ Connected
```

- 回歸：`claude -p "/english-tutor-plugin:english-check She have two cat."` → 雲端 id 50、`source = skill`；本機資料庫沒有新增，確認走的是 Lightsail。Hook 用同一個註冊，不用改。
- 風險：05 之前 API key 以明文經 HTTP 走公網。資料只是英文句子，且 key 可隨時在伺服器 `.env` 換掉並 `up -d` 重啟。
- 05 設好網域後，只要把上面的網址換成 `https://<domain>/mcp` 再跑一次 `claude mcp remove` / `add`。
- 本機的 `docker compose --profile http` mcp 容器此時不再被 Claude Code 使用，可停掉；要回本機開發時把網址換回 `http://localhost:8001/mcp` 與 `dev-local-key`。
- 同日稍後：連線設定改由 plugin 的 `.mcp.json` 提供（見 [mac-step/06](../mac-step/06-claude-hook.md) 的晚間紀錄），`claude mcp add` 的 local scope 註冊已移除。之後換網域只要改 plugin 的 `.mcp.json` 並升版。
