# 在 Lightsail Ubuntu 上安裝 XFCE 桌面（xrdp 遠端桌面）

## 目標

在現有的 Tokyo Lightsail 實例（Ubuntu 24.04，2 vCPU / 4 GB，$24 方案）裝一個輕量的 XFCE 桌面，
從 Mac 用「Windows App」（舊名 Microsoft Remote Desktop）透過 **SSH tunnel** 連進去看圖形介面。
不開新的防火牆 port，Lightsail 防火牆維持只開 22/80/443。

## 先看清楚再裝

| 項目 | 數字 | 說明 |
|------|------|------|
| 記憶體 | XFCE + xrdp 閒置約 300–500 MB | 4 GB 機器五個容器閒置約用 750 MB，桌面開著還有餘裕；build 時仍可能碰到 swap |
| 磁碟 | 約 1–1.5 GB | 60 GB 磁碟沒問題 |
| 安全 | 3389 不對外開 | 一律走 SSH tunnel，xrdp 只在本機監聽 |

> 建議：桌面只在需要時連，用完登出。2026-11-07 已從 $12（2 GB）升到 $24（4 GB），就是為了容得下桌面。
> 若之後常駐使用，可另開一台 $7 實例專門當桌面，不要跟正式服務擠同一台。

## 前置條件

- [02](02-lightsail-instance.md) 與 [03](03-server-setup.md) 完成（swap 已開，`free -h` 看得到 2 GB swap）。
- Mac 已從 App Store 安裝 **Windows App**（Microsoft 的 RDP 客戶端）。
- 本機可用 `ssh english-tutor`（即 `ubuntu@35.79.82.165`）登入。

## 步驟

### 1. 裝 XFCE（最小安裝）

機器上：

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y --no-install-recommends xfce4 xfce4-terminal dbus-x11
```

> 不要裝 `xubuntu-desktop`，那會拉進 LibreOffice、印表機、藍牙等用不到的東西，多佔 2–3 GB。
> 要檔案管理員、截圖、音量等小工具再補 `sudo apt install -y xfce4-goodies`（約多 300 MB）。

### 2. 裝 xrdp 並只監聽本機

```bash
sudo apt install -y xrdp
sudo adduser xrdp ssl-cert
sudo sed -i 's/^port=3389/port=tcp:\/\/127.0.0.1:3389/' /etc/xrdp/xrdp.ini
sudo systemctl enable --now xrdp
sudo systemctl status xrdp --no-pager
```

確認只有 127.0.0.1 在監聽：

```bash
ss -tlnp | grep 3389        # 應看到 127.0.0.1:3389，不是 0.0.0.0:3389
```

### 3. 建立桌面用的使用者

不要用 `ubuntu`（它是 sudo 免密碼的管理帳號），另外開一個一般使用者給桌面登入：

```bash
sudo adduser desktop          # 會問密碼，xrdp 登入要用
echo "xfce4-session" | sudo tee /home/desktop/.xsession
sudo chown desktop:desktop /home/desktop/.xsession
```

> 如果真的要用 `ubuntu` 登入，先 `sudo passwd ubuntu` 設密碼，再對 `/home/ubuntu/.xsession` 做同樣設定。

### 4. 關掉登入後的 polkit 認證視窗（Ubuntu 24.04 常見）

xrdp 登入 XFCE 後常跳出「Authentication Required to Create Managed Color Device」，加一條規則讓它閉嘴：

```bash
sudo tee /etc/polkit-1/rules.d/45-allow-colord.rules >/dev/null <<'RULE'
polkit.addRule(function(action, subject) {
  if ((action.id == "org.freedesktop.color-manager.create-device" ||
       action.id == "org.freedesktop.color-manager.create-profile" ||
       action.id == "org.freedesktop.color-manager.delete-device" ||
       action.id == "org.freedesktop.color-manager.delete-profile" ||
       action.id == "org.freedesktop.color-manager.modify-device" ||
       action.id == "org.freedesktop.color-manager.modify-profile") &&
      subject.isInGroup("users")) {
    return polkit.Result.YES;
  }
});
RULE
sudo systemctl restart xrdp
```

### 5. Mac 端：開 SSH tunnel 再用 RDP 連

本機終端機（連線期間要一直開著）：

```bash
ssh -N -L 3389:localhost:3389 ubuntu@35.79.82.165
```

然後 Windows App → `+` → PC：

| 欄位 | 值 |
|------|----|
| PC name | `localhost:3389` |
| User account | `desktop` 與步驟 3 設的密碼 |

連上後 xrdp 的綠色登入畫面 Session 選 **Xorg**，輸入帳密，就會進 XFCE。

> 想省事可以在 `~/.ssh/config` 加：
>
> ```
> Host lightsail-desktop
>     HostName 35.79.82.165
>     User ubuntu
>     LocalForward 3389 localhost:3389
> ```
>
> 之後只要 `ssh -N lightsail-desktop`。

### 6. 驗證

```bash
free -h                      # 看桌面登入後還剩多少記憶體
docker compose -f /srv/english-tutor/docker-compose.prod.yml ps   # 五個容器仍 Up / healthy
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/         # 200
```

## 常見問題

- **RDP 連上後黑畫面或馬上斷線**：`.xsession` 內容必須是 `xfce4-session`，且擁有者是該使用者；
  看 `/var/log/xrdp-sesman.log` 與 `~/.xorgxrdp.*.log`。
- **登入要很久**：`sudo systemctl restart xrdp`，或檢查是否有上次沒登出的殘留 session（`loginctl list-sessions`）。
- **記憶體不夠、容器被 OOM kill**：桌面不用時從 XFCE 登出（不是只關 RDP 視窗），session 會跟著結束；
  或 `sudo systemctl stop xrdp` 先停掉，要用再開。
- **要瀏覽器**：`sudo apt install -y firefox`（snap 版），但 2 GB 機器上 Firefox 會很吃力，
  Chromium 也一樣；建議只拿桌面做輕量設定，不要在上面上網。

## 移除

```bash
sudo systemctl disable --now xrdp
sudo apt purge -y xrdp xfce4 xfce4-terminal xfce4-goodies
sudo apt autoremove -y
sudo deluser --remove-home desktop
sudo rm -f /etc/polkit-1/rules.d/45-allow-colord.rules
```

## 完成條件

- [ ] `ss -tlnp | grep 3389` 只看到 `127.0.0.1:3389`
- [ ] Mac 透過 SSH tunnel + Windows App 能看到 XFCE 桌面
- [ ] 桌面登入後五個容器仍 healthy，`free -h` 可用記憶體 + swap 沒有見底
