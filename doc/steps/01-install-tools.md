# 01. 安裝基礎工具

## 目標

把 Docker、Python、Node.js 開發環境裝好，讓後續每一步都能在本機執行。

## 目前狀態（2026-11-01 檢查）

| 工具 | 狀態 |
|------|------|
| Git 2.55 | ✅ 已安裝 |
| Claude Code 2.1.302 | ✅ 已安裝 |
| WSL2 | ❌ 未安裝 |
| Docker Desktop | ❌ 未安裝 |
| Python 3.12.10 / uv 0.13.6 | ✅ 已安裝（2026-11-01） |
| Node.js 26.13.0 / npm 11.20.0 | ✅ 已安裝（2026-11-01） |

## 步驟

依序執行，**每裝完一項就開新的終端機**再驗證，否則 PATH 不會更新。

### 1-1. WSL2

以系統管理員身分開 PowerShell：

```powershell
wsl --install
```

- 裝完必須重新開機。
- 重開後會自動跳出 Ubuntu 視窗，設定使用者名稱與密碼。
- 驗證：

```powershell
wsl --status
wsl -l -v        # Ubuntu 應顯示 VERSION 2
```

### 1-2. Docker Desktop

- 下載：https://www.docker.com/products/docker-desktop/
- 安裝時勾選「Use WSL 2 instead of Hyper-V」。
- 開啟 Docker Desktop → Settings → General，確認「Use the WSL 2 based engine」已勾選。
- Settings → Resources → WSL Integration，開啟 Ubuntu 整合。
- 驗證：

```powershell
docker --version
docker compose version
docker run hello-world
```

### 1-3. Python 3.12 與 uv

```powershell
winget install Python.Python.3.12
winget install astral-sh.uv
```

- 到 Settings → Apps → Advanced app settings → App execution aliases，把 `python.exe` 與 `python3.exe` 的 Microsoft Store 捷徑**關掉**（否則打 `python` 會跳到商店）。
- 驗證：

```powershell
python --version
uv --version
```

### 1-4. Node.js LTS

```powershell
winget install OpenJS.NodeJS.LTS
```

驗證：

```powershell
node --version
npm --version
```

### 1-5. Windows 設定（選用但建議）

- 在 `%UserProfile%\.wslconfig` 限制 Docker 記憶體：

```ini
[wsl2]
memory=4GB
```

- 第一次啟動 Docker Desktop 或 Vite 跳出防火牆詢問時，允許「私人網路」。

## 完成條件

- [ ] `wsl -l -v` 看到 Ubuntu，VERSION 為 2
- [ ] `docker run hello-world` 成功印出 Hello from Docker!
- [x] `python --version` 顯示 3.12.x
- [x] `uv --version` 正常
- [x] `node --version` 顯示 v22 或以上（LTS）

## 下一步

→ [02-docker-postgres.md](02-docker-postgres.md)

## 實作紀錄

### 2026-11-01（Claude Code 協助）

**已完成：**
- `winget install Python.Python.3.12` → Python 3.12.10，裝在 `%LocalAppData%\Programs\Python\Python312`。
- `winget install astral-sh.uv` → uv 0.13.6。
- `winget install OpenJS.NodeJS.LTS` → Node.js 26.13.0、npm 11.20.0（UAC 提示後完成）。
- 建立 `%UserProfile%\.wslconfig`（memory=4GB）。
- 開新終端機驗證：`python --version`、`py -3.12 --version`、`uv --version`、`node --version`、`npm --version` 皆正常。
  新裝的 Python 在 PATH 排在 Microsoft Store 別名之前，所以 `python` 已指到正確版本；
  App execution aliases 仍建議手動關掉以免日後 PATH 變動。

**無法由 Claude Code 完成（需要系統管理員）：**
- WSL2：`wsl --install` 與 `winget install Microsoft.WSL` 都回報需要管理員權限（0x80073d28）。
  → 請以系統管理員身分開 PowerShell 執行 `wsl --install`，然後重開機。
- Docker Desktop：`winget install Docker.DockerDesktop` 安裝程式在提升權限階段失敗（exit 4294967291），
  且 WSL2 尚未就緒。→ 先裝好 WSL2 並重開機後，再手動安裝 Docker Desktop。
