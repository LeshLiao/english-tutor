# 02. 伺服器基本設定

## 目標

系統更新、只開 22/80/443、加 swap、把 repo clone 到 VPS、建立正式版 `.env`。

## 前置條件

- [01](01-buy-vps.md) 完成，可用金鑰 SSH 登入。

## 步驟

### 2-1. 系統更新與基本工具

```bash
apt update && apt upgrade -y
apt install -y git ufw fail2ban unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades    # 選 Yes，自動裝安全更新
timedatectl set-timezone Asia/Taipei
```

### 2-2. 防火牆（兩層）

**hPanel 防火牆**（VPS → Security → Firewall）建一組規則並套用到這台：

| 動作 | 協定 | Port | 來源 |
|------|------|------|------|
| Accept | TCP | 22 | 你的 IP（或 any，有金鑰與 fail2ban 保護） |
| Accept | TCP | 80 | any |
| Accept | TCP | 443 | any |
| Drop | any | any | any（預設） |

**機器內 ufw**（與上面相同，雙重保險）：

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status
```

> Docker 會自己改 iptables 繞過 ufw，所以 **compose 裡除了 caddy 以外的服務都不要寫 `ports:`**（03 會處理），否則 5432/8000/8001 還是會曝露在外。

### 2-3. Swap（4 GB RAM 夠用，但保險起見加 2 GB）

```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
free -h
```

### 2-4. 建立部署用的目錄與 repo

```bash
mkdir -p /srv && cd /srv
git clone https://github.com/<你的帳號>/english-tutor.git
cd english-tutor
```

- 私有 repo：在 VPS 上 `ssh-keygen -t ed25519`，把公鑰加到 GitHub repo 的 Deploy keys（唯讀），再用 `git@github.com:...` clone。
- 確認 `.gitattributes` 有 `* text=auto eol=lf`，否則 Windows 上 commit 的 shell script 在容器裡會因 CRLF 出錯。

### 2-5. 正式版 `.env`

```bash
cp .env.example .env
nano .env
```

內容（全部換掉本機的值）：

```
POSTGRES_USER=english
POSTGRES_PASSWORD=<openssl rand -base64 24 產生>
POSTGRES_DB=english_practice
API_KEY=<openssl rand -hex 32 產生>
DOMAIN=<你的網域，例如 english.example.com>
```

```bash
chmod 600 .env
```

> `.env` 已在 `.gitignore`，不會進 git。API_KEY 之後要填到 Claude Code 與 Caddyfile，先抄一份到密碼管理器。

## 完成條件

- [ ] `ufw status` 只有 22/80/443 allow
- [ ] hPanel 防火牆規則已套用
- [ ] `free -h` 看到 2 GB swap
- [ ] `/srv/english-tutor/.env` 存在、權限 600、密碼與 API key 皆為新產生

## 下一步

→ [03-compose-prod.md](03-compose-prod.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）
