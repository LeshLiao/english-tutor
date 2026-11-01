# 05. 網域、Route 53、Caddy 反向代理與 HTTPS

## 目標

網域指向 Lightsail 靜態 IP，Caddy 自動取得 Let's Encrypt 憑證，`/api`、`/mcp`、`/` 三條路徑都走 HTTPS；
前端不再內含 API key，改由 Caddy 注入並加基本認證保護。

## 前置條件

- [04](04-compose-prod.md) 完成，用 IP 可看到前端。
- 有一個網域，或準備在這一步買。

## 步驟

### 5-1. DNS：三種做法選一種

**做法 1：網域在既有註冊商（最省，$0）**

在註冊商的 DNS 管理加一筆：

| 類型 | 名稱 | 值 | TTL |
|------|------|----|-----|
| A | `english`（或 `@`） | `<STATIC_IP>` | 300 |

**做法 2：網域在別處，DNS 交給 Route 53（$0.50/月）**

1. Route 53 → Hosted zones → Create，輸入網域（例如 `example.com`），類型 Public。
2. 把 Route 53 給的 4 個 NS 伺服器填回註冊商的 nameserver 設定。
3. 在 hosted zone 加 A record：`english.example.com` → `<STATIC_IP>`。

只有一個 A record 的話做法 1 就夠；之後要用 ACM 憑證、ALB（方案 C）時再搬到 Route 53。

**做法 3：直接在 Route 53 買網域**

Route 53 → Registered domains → Register，`.com` 約 $14–15/年，會自動建 hosted zone（$0.50/月）。
適合完全不想碰其他註冊商的人。

> Lightsail 自己也有 DNS zone 功能（Networking → DNS zones，免費），但功能很陽春，用上面三種之一即可。

等生效：

```powershell
nslookup english.example.com
```

> 若用 Cloudflare，不要開橘雲（proxy），否則 Let's Encrypt 的 HTTP 驗證會被擋；要用的話改 DNS-only。

### 5-2. 正式 Caddyfile

內容與 Hostinger 版相同，請照 [hostinger/04-domain-caddy-https.md](../hostinger/04-domain-caddy-https.md) 的 4-2 把 `deploy/Caddyfile` 換成網域版：

- `{$DOMAIN}` 區塊、`encode gzip`。
- `/api/*` 與前端：basic auth 保護，由 Caddy 注入 `X-API-Key`，前端 bundle 不含 key。
- `/mcp*`：不套 basic auth，由 Claude Code 自帶 `X-API-Key`，mcp 容器驗證。

產生 bcrypt 雜湊：

```bash
docker run --rm caddy:2 caddy hash-password --plaintext '<你的密碼>'
```

### 5-3. 套用

```bash
cd /srv/english-tutor
git pull
docker compose -f docker-compose.prod.yml up -d --force-recreate caddy
docker compose -f docker-compose.prod.yml logs -f caddy   # 看到 certificate obtained 即成功
```

Let's Encrypt 需要從外部連到 80 與 443，02-4 的 Lightsail 防火牆兩個都要開著。

### 5-4. 驗證

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
- [ ] 前端三頁可用，且 bundle 內搜不到 API key
- [ ] `/mcp` 沒帶 key 回 401，帶對的 key 不是 401

## 下一步

→ [06-claude-connect.md](06-claude-connect.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）
