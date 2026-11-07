# 03. 伺服器基本設定

## 目標

系統更新、自動安全更新、加 swap、把 repo clone 到機器上、建立正式版 `.env`。

與 [hostinger/02-server-setup.md](../hostinger/02-server-setup.md) 幾乎相同，差異只有：
Lightsail 的防火牆在 Console 設（02 已做），機器內可不裝 ufw；記憶體只有 2 GB（2026-11-07 後為 4 GB），swap 一定要加。

## 前置條件

- [02](02-lightsail-instance.md) 完成，可用金鑰 SSH 登入。

## 步驟

以下指令都在 `sudo -i` 之後以 root 執行。

### 3-1. 系統更新與基本工具

```bash
apt update && apt upgrade -y
apt install -y git fail2ban unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades    # 選 Yes；不想跳選單可用 dpkg-reconfigure -f noninteractive unattended-upgrades
timedatectl set-timezone Asia/Taipei
[ -f /var/run/reboot-required ] && reboot    # 有更新 kernel 時會要求重開，約 30 秒
```

> Ubuntu 24.04 的 `apt upgrade` 會跳 needrestart 的服務重啟選單；用 `ssh` 批次執行時先 `export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a`。

### 3-2. 防火牆

Lightsail Console 的防火牆（02-4）已經是第一道門，而且在實例之外，Docker 改 iptables 也繞不過它，
所以**不需要**再裝 ufw。

仍要遵守：**compose 裡除了 caddy 以外的服務都不要寫 `ports:`**（04 會處理）。
就算 Lightsail 防火牆擋住，也不要讓 5432/8000/8001 在機器上監聽公開介面。

### 3-3. Swap（2 GB RAM 必加；升到 4 GB 後仍保留）

```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
sysctl vm.swappiness=10
echo 'vm.swappiness=10' >> /etc/sysctl.d/99-swap.conf
free -h
```

> frontend 的 `npm run build` 在 2 GB 機器上會用到 swap，屬正常；跑完就釋放。

### 3-4. 建立部署用的目錄與 repo

```bash
mkdir -p /srv && cd /srv
git clone https://github.com/<你的帳號>/english-tutor.git
cd english-tutor
```

- 私有 repo：在機器上 `ssh-keygen -t ed25519`，把公鑰加到 GitHub repo 的 Deploy keys（唯讀），再用 `git@github.com:...` clone。
- 建議仍放 `.gitattributes` 設 `* text=auto eol=lf`，之後若有人在 Windows 上 commit shell script 才不會因 CRLF 在容器裡出錯。

### 3-5. 正式版 `.env`

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

- [x] `apt upgrade` 完成，`unattended-upgrades` 啟用
- [x] `free -h` 看到 2 GB swap
- [x] `/srv/english-tutor/.env` 存在、權限 600、密碼與 API key 皆為新產生（2026-11-02）
- [x] 時區為 Asia/Taipei

## 下一步

→ [04-compose-prod.md](04-compose-prod.md)

## 實作紀錄

**2026-11-01**（前半段：3-1 到 3-3）

- 從 Mac 以 `ssh english-tutor 'sudo bash -s' <<EOF` 批次執行，設 `DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a` 避免互動選單。
- `apt upgrade` 後 `/var/run/reboot-required` 存在，`sudo reboot` 約 15 秒回來，kernel 7.0.0-1012-aws。
- git 2.43.0、fail2ban active、`20auto-upgrades` 兩項皆為 1。
- 2 GB `/swapfile` 已掛載並寫入 fstab，`vm.swappiness=10`；時區 Asia/Taipei。
- 3-4 clone repo 與 3-5 `.env` 尚未做：repo 目前只有 `doc/`，等 backend / mcp-server / frontend 程式碼完成後再補。

**2026-11-02**（後半段：3-4 到 3-5，透過 cmux 裡已登入的 SSH 面板操作）

- `/srv/english-tutor` 改為 `chown ubuntu:ubuntu`，用一般帳號 clone 與之後 `git pull`、`docker compose`（ubuntu 已在 docker 群組）。
- repo 公開，`git clone https://github.com/LeshLiao/english-tutor.git .`（f7edba0）。
- `.env` 由 `openssl rand` 在伺服器上產生，`chmod 600`；多了 `CORS_ORIGINS=`（同源不需要）與 `DOMAIN=`（05 再填）兩個空值。
- 完整過程見 [local-to-lightsail.md](local-to-lightsail.md)。
