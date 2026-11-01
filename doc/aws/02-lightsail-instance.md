# 02. 建立 Lightsail 實例與首次登入

## 目標

在 Oregon 建一台 Lightsail $12 實例（Ubuntu 24.04），掛靜態 IP，防火牆只開 22/80/443，用 SSH 金鑰登入並裝好 Docker。

## 前置條件

- [01](01-account-region-budget.md) 完成。
- 本機已有 SSH 金鑰；沒有就先產生：

```powershell
ssh-keygen -t ed25519 -C "english-tutor"
Get-Content $env:UserProfile\.ssh\id_ed25519.pub   # 等一下要貼到 Lightsail
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
| Region / Zone | **Oregon (us-west-2)**, Zone A | 01 決定的區域 |
| Platform | Linux/Unix | |
| Blueprint | **OS Only → Ubuntu 24.04 LTS** | 不要選 Apps（例如 Docker 範本不存在，WordPress 等用不到） |
| Launch script | 留空 | Docker 在 2-6 手動裝，比較好除錯 |
| SSH key pair | `english-tutor`（2-1 上傳的） | |
| Network type | Dual-stack（IPv4 + IPv6） | 含公開 IPv4，不另外收費 |
| Plan | **$12 USD**（2 GB RAM、2 vCPU、60 GB SSD、3 TB 流量） | $7（1 GB）跑五個容器加 build 會很吃緊 |
| Name | `english-tutor` | |

建立後等狀態變成 Running（約 1–2 分鐘）。

### 2-3. 靜態 IP

Networking → Create static IP → 選 Oregon → 附加到 `english-tutor`，名稱 `english-tutor-ip`。

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

```powershell
ssh ubuntu@<STATIC_IP>
```

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

Lightsail 實例是 x86_64，映像檔與本機 Docker Desktop build 出來的相同，不需要處理 ARM。

### 2-7. 關閉密碼登入（Lightsail 預設已關，確認即可）

```bash
grep -E '^PasswordAuthentication' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/* 2>/dev/null
```

看到 `no` 即可。Lightsail Console 的「Connect using SSH」瀏覽器終端機是最後救援手段，不受此設定影響。

## 完成條件

- [ ] Lightsail 顯示實例 Running，區域 Oregon，方案 $12
- [ ] 靜態 IP 已附加，`curl checkip` 結果一致
- [ ] 防火牆只有 22/80/443
- [ ] `ssh ubuntu@<STATIC_IP>` 以金鑰登入成功
- [ ] `docker compose version` 正常

## 下一步

→ [03-server-setup.md](03-server-setup.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）
