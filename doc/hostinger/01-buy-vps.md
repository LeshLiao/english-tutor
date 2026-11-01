# 01. 購買 VPS 與首次登入

## 目標

買一台 Hostinger KVM 1，選 Docker 範本與離台灣最近的機房，用 SSH 金鑰登入成功。

## 前置條件

- [總覽](00-README.md) 前置條件達成。
- 本機已有 SSH 金鑰；沒有就先產生：

```powershell
ssh-keygen -t ed25519 -C "english-tutor"
Get-Content $env:UserProfile\.ssh\id_ed25519.pub   # 等一下要貼到 Hostinger
```

## 步驟

### 1-1. 選方案

- 到 https://www.hostinger.com/vps-hosting 選 **KVM 1**（1 vCPU / 4 GB / 50 GB NVMe）。
- 計費期：促銷價只有 24 個月一次付清才有（約 $155.76）；沒有月繳價。
  若不想一次付兩年，先接受較高的短期價，或先確認當下頁面是否有 12 個月選項。
- 不需要加購任何附加服務（備份、管理服務等）。

### 1-2. 設定精靈

購買後 hPanel 會跳出 VPS 設定精靈，依序選：

| 項目 | 選擇 | 說明 |
|------|------|------|
| 機房 | **Malaysia（Kuala Lumpur）** | 離台灣最近；其次 Indonesia。機房設定後不能換，只能備份後重灌 |
| 作業系統 | **OS with Control Panel → Docker**（Ubuntu 24.04 + Docker） | 內建 docker-ce 與 docker compose，之後不用自己裝 |
| root 密碼 | 設一組強密碼 | 只在救援時用，平常用金鑰 |
| SSH key | 貼上 `id_ed25519.pub` 內容 | 之後 `ssh root@<ip>` 不用密碼 |
| 惡意軟體掃描 | 開啟即可 | 免費，不影響效能 |

> 若精靈裡找不到 Docker 範本，先選一般 Ubuntu 24.04，之後在 hPanel → VPS → OS & Panel → Operating System 換成 Docker 範本（會清空機器，所以要在這一步就換好）。

### 1-3. 首次登入

等 hPanel 顯示 VPS 為 Running，記下 IP：

```powershell
ssh root@<VPS_IP>
```

登入後確認：

```bash
cat /etc/os-release | head -2      # Ubuntu 24.04
docker --version
docker compose version
free -h                            # 約 3.8 GB 可用
df -h /                            # 約 50 GB
```

### 1-4. 關閉密碼登入（建議）

確認金鑰登入成功後：

```bash
sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh
```

> 先開第二個終端機測試金鑰登入沒問題再關，免得把自己鎖在外面。hPanel 的瀏覽器終端機是最後救援手段。

## 完成條件

- [ ] hPanel 顯示 VPS Running，機房為 Malaysia（或 Indonesia）
- [ ] `ssh root@<VPS_IP>` 以金鑰登入成功
- [ ] `docker compose version` 正常
- [ ] 密碼登入已關閉

## 下一步

→ [02-server-setup.md](02-server-setup.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）
