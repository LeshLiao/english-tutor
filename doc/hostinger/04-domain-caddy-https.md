# 04. 網域、Caddy 反向代理與 HTTPS

## 目標

網域指向 VPS，Caddy 自動取得 Let's Encrypt 憑證，`/api`、`/mcp`、`/` 三條路徑都走 HTTPS；
前端不再內含 API key，改由 Caddy 注入並加基本認證保護。

## 前置條件

- [03](03-compose-prod.md) 完成，用 IP 可看到前端。
- 有一個網域。

## 步驟

### 4-1. DNS

在網域的 DNS 管理（Hostinger hPanel → Domains → DNS，或其他註冊商）加一筆：

| 類型 | 名稱 | 值 | TTL |
|------|------|----|-----|
| A | `english`（或 `@`） | `<VPS_IP>` | 300 |

等生效：

```powershell
nslookup english.example.com
```

> 不要在 Cloudflare 開橘雲（proxy），否則 Let's Encrypt 的 HTTP 驗證會被擋；要用的話改 DNS-only。

### 4-2. 正式 Caddyfile

把 `deploy/Caddyfile` 換成：

```
{$DOMAIN} {
    encode gzip

    # 前端 + API：用 basic auth 保護，API key 由 Caddy 注入，前端 bundle 不含 key
    @app path / /assets/* /sentences* /api/*
    handle @app {
        basic_auth {
            <使用者名稱> <bcrypt 雜湊，見下方>
        }
        handle /api/* {
            uri strip_prefix /api
            reverse_proxy backend:8000 {
                header_up X-API-Key {$API_KEY}
            }
        }
        handle {
            reverse_proxy frontend:80
        }
    }

    # MCP：Claude Code 自己帶 X-API-Key，由 mcp 容器驗證，不套 basic auth
    handle /mcp* {
        reverse_proxy mcp:8001
    }
}
```

產生 bcrypt 雜湊：

```bash
docker run --rm caddy:2 caddy hash-password --plaintext '<你的密碼>'
```

`{$DOMAIN}` 與 `{$API_KEY}` 來自 compose 裡 caddy 服務的 `environment`（03 已加）。

> 前端路由若之後新增頁面，記得補進 `@app` 的 path 清單；或改成「除了 `/mcp*` 以外全部」的寫法。

### 4-3. 套用

```bash
cd /srv/english-tutor
git pull
docker compose -f docker-compose.prod.yml up -d --force-recreate caddy
docker compose -f docker-compose.prod.yml logs -f caddy   # 看到 certificate obtained 即成功
```

### 4-4. 驗證

```powershell
curl.exe -I https://english.example.com/            # 401（需 basic auth）
curl.exe -I http://english.example.com/             # 308 → https
curl.exe -u user:pass https://english.example.com/api/docs
curl.exe -I https://english.example.com/mcp         # 401（沒帶 X-API-Key）
curl.exe -I -H "X-API-Key: <API_KEY>" https://english.example.com/mcp   # 不是 401
```

瀏覽器開 `https://english.example.com`，輸入 basic auth 帳密後，三個頁面的資料應與 API 一致。

## 完成條件

- [ ] 瀏覽器顯示鎖頭，憑證為 Let's Encrypt
- [ ] `http://` 自動轉 `https://`
- [ ] 前端三頁可用，且 bundle 內搜不到 API key（`curl` 下載 `assets/*.js` 後 grep）
- [ ] `/mcp` 沒帶 key 回 401，帶對的 key 不是 401

## 下一步

→ [05-claude-connect.md](05-claude-connect.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）
