# 02. 建立 Lightsail 實例與首次登入

## 目標

建一台 Lightsail 實例（Ubuntu 24.04），掛靜態 IP，防火牆只開 22/80/443，用 SSH 金鑰登入並裝好 Docker。

> 本文以起步時的 Oregon $12 寫成。2026-11-07 已用快照搬到 **Tokyo $24**（靜態 IP `35.79.82.165`），見 [oregon-to-tokyo.md](oregon-to-tokyo.md)；
> 重做時區域選 Tokyo、方案選 $24，其餘步驟相同。

## 前置條件

- [01](01-account-region-budget.md) 完成。
- 本機已有 SSH 金鑰；沒有就先產生：

```bash
ssh-keygen -t ed25519 -C "english-tutor"
cat ~/.ssh/id_ed25519.pub | pbcopy      # 直接複製到剪貼簿，等一下貼到 Lightsail
```

## 步驟

### 2-1. 上傳 SSH 公鑰

Lightsail Console（https://lightsail.aws.amazon.com）→ Account → SSH keys → Upload new：
選區域 Oregon，貼上 `id_ed25519.pub` 內容，名稱 `english-tutor`。

> 也可以用 Lightsail 預設金鑰（會下載一個 `.pem`），但自己的金鑰比較好管理。

### 2-2. 建立實例

Lightsail → Instances → Create instance：

| 項目 | 選擇 | 說明 |
|------|------|------|
| Region / Zone | **Tokyo (ap-northeast-1)**, Zone A（起步時為 Oregon） | 01 決定的區域 |
| Platform | Linux/Unix | |
| Blueprint | **OS Only → Ubuntu 24.04 LTS** | 不要選 Apps（例如 Docker 範本不存在，WordPress 等用不到） |
| Launch script | 留空 | Docker 在 2-6 手動裝，比較好除錯 |
| SSH key pair | `english-tutor`（2-1 上傳的） | |
| Network type | Dual-stack（IPv4 + IPv6） | 含公開 IPv4，不另外收費 |
| Plan | **$24 USD**（4 GB RAM、2 vCPU、80 GB SSD、4 TB 流量） | 起步用 $12（2 GB）跑五個容器可以，但 build 與桌面會吃 swap；$7（1 GB）不夠 |
| Name | `Ubuntu-english-tutor` | |

建立後等狀態變成 Running（約 1–2 分鐘）。

### 2-3. 靜態 IP

Networking → Create static IP → 選與實例相同的區域 → 附加到實例，名稱 `english-tutor-ip`（Tokyo 版現為 `35.79.82.165`）。

- 附加在實例上的靜態 IP **免費**；沒附加的會收 $0.005/小時（約 $3.65/月），實例刪掉時記得一起刪 IP。
- 記下這個 IP，之後 DNS 會指到這裡。

### 2-4. 防火牆

實例頁 → Networking → IPv4 Firewall（預設只有 SSH 22 與 HTTP 80）：

| 應用 | 協定 | Port | 來源 |
|------|------|------|------|
| SSH | TCP | 22 | 建議勾「Restrict to IP address」填自己的 IP；浮動 IP 的話開 any，靠金鑰與 fail2ban |
| HTTP | TCP | 80 | any（Caddy 取憑證與 HTTP→HTTPS 轉向用） |
| HTTPS | TCP | 443 | any（**要手動加**） |

IPv6 Firewall 同樣加 443。其他全部不開。

### 2-5. 首次登入

```bash
ssh ubuntu@<STATIC_IP>
```

**若建立實例時 SSH key pair 選的是 Lightsail 預設金鑰**（而不是 2-1 上傳的），要先把預設私鑰下載到本機：
Account → SSH keys → Default keys → Oregon → Download，然後：

```bash
mv ~/Downloads/LightsailDefaultKey-us-west-2.pem ~/.ssh/
chmod 400 ~/.ssh/LightsailDefaultKey-us-west-2.pem
```

在 `~/.ssh/config` **最前面**加一段（放在任何 `Host *` 之前），之後打 `ssh english-tutor` 就能登入：

```
Host english-tutor
    HostName <STATIC_IP>
    User ubuntu
    IdentityFile ~/.ssh/LightsailDefaultKey-us-west-2.pem   # 用自己的金鑰則改 ~/.ssh/id_ed25519
    IdentitiesOnly yes
```

> `IdentitiesOnly yes` 是為了避免 `Host *` 區塊指定的其他金鑰先被送出去而被拒絕。
> 後續文件中的 `ssh ubuntu@<STATIC_IP>` 都可用 `ssh english-tutor` 取代，`scp` 同理。

> Lightsail Ubuntu 的預設使用者是 `ubuntu`，不是 `root`；需要 root 時用 `sudo`。
> 之後文件中的指令都以 `sudo -i` 切到 root 後執行，與 Hostinger 版一致。

登入後確認：

```bash
sudo -i
cat /etc/os-release | head -2      # Ubuntu 24.04
nproc; free -h; df -h /            # 2 vCPU、約 1.9 GB、約 58 GB
curl -s https://checkip.amazonaws.com   # 應等於靜態 IP
```

### 2-6. 安裝 Docker（官方 apt 來源）

```bash
apt update && apt install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt update && apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
usermod -aG docker ubuntu
docker --version
docker compose version
docker run --rm hello-world
```

Lightsail 實例是 x86_64。本文件的映像都在這台機器上 build，所以不用管架構；
若之後想在 Apple Silicon 的 Mac 上 build 再推上去，要加 `--platform linux/amd64`，否則會 build 出 ARM 映像跑不起來。

### 2-7. 關閉密碼登入（Lightsail 預設已關，確認即可）

```bash
grep -E '^PasswordAuthentication' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/* 2>/dev/null
```

看到 `no` 即可。Lightsail Console 的「Connect using SSH」瀏覽器終端機是最後救援手段，不受此設定影響。

## 完成條件

- [x] Lightsail 顯示實例 Running，區域 Oregon，方案 $12（2026-11-07 起：Tokyo，$24）
- [x] 靜態 IP 已附加，`curl checkip` 結果一致
- [x] 防火牆只有 22/80/443
- [x] `ssh english-tutor` 以金鑰登入成功
- [x] `docker compose version` 正常

## 下一步

→ [03-server-setup.md](03-server-setup.md)

## 實作紀錄

**2026-11-01**

- 實例 `Ubuntu-english-tutor`，Oregon Zone A，Ubuntu 24.04.4 LTS，靜態 IP `44.228.11.180`（已於 2026-11-07 搬到 Tokyo，新 IP `35.79.82.165`）。
- 建立時 SSH key pair 誤選 Lightsail 預設金鑰，用自己上傳的 `id_ed25519` 登入被拒。
  解法：下載 `LightsailDefaultKey-us-west-2.pem` 到 `~/.ssh/`，`chmod 400`，`~/.ssh/config` 加 `Host english-tutor` 並設 `IdentitiesOnly yes`
  （本機 `Host *` 原本指定了另一把金鑰，不加 `IdentitiesOnly` 會一直送錯）。機器上的 `authorized_keys` 未動。
- Docker 以官方 apt 來源安裝完成：Docker 29.9.2、Compose v5.6.1，`hello-world` 正常。密碼登入預設已關（`60-cloudimg-settings.conf`）。
- 登入畫面提示 `New release '26.04.1 LTS' available`，**不要**跑 `do-release-upgrade`，維持 24.04。
