# 01. 安裝基礎工具（macOS）

## 目標

把 Docker、Python、Node.js 開發環境裝好，讓後續每一步都能在本機執行。

## 目前狀態（2026-11-02 檢查）

| 工具 | 狀態 |
|------|------|
| macOS 26.6.2（Apple Silicon / arm64） | ✅ |
| Homebrew 7.0.9 | ✅ 已安裝 |
| Git 2.40.0（Homebrew） | ✅ 已安裝 |
| Claude Code 2.1.280 | ✅ 已安裝 |
| Docker Desktop（Docker 29.8.2 / Compose v5.5.1） | ✅ 已安裝並可執行（2026-11-02） |
| uv 0.11.25（Homebrew） | ✅ 已安裝 |
| Python 3.12.13（由 uv 管理） | ✅ 已安裝，但**不在 PATH**，需透過 `uv run` 使用 |
| Homebrew python3 | 3.15.0（版本太新，本專案不用它） |
| Node.js 26.12.0 / npm 11.20.0 | ✅ 已安裝 |

macOS 不需要 WSL2，這是與 Windows 版最大的差異。

## 步驟

依序執行。Homebrew 裝完的東西通常立刻可用；若指令找不到，**開新的終端機分頁**再試。

### 1-1. Homebrew

已安裝可跳過。未安裝時：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

裝完依畫面提示把 `eval "$(/opt/homebrew/bin/brew shellenv)"` 加進 `~/.zprofile`。

驗證：

```bash
brew --version
```

### 1-2. Docker Desktop

二選一：

**A. Docker Desktop for Mac（本機目前使用）**

```bash
brew install --cask docker
```

- 第一次要從「應用程式」手動開啟 Docker.app，同意授權，等左下角顯示 Engine running。
- Settings → Resources，把 Memory 調到 4 GB 左右即可（取代 Windows 的 `.wslconfig`）。
- Settings → General，建議開啟「Start Docker Desktop when you sign in」，否則每次重開機都要手動啟動，`docker compose up` 會報 `Cannot connect to the Docker daemon`。

**B. OrbStack（選用，較省資源）**

```bash
brew install --cask orbstack
```

OrbStack 提供相容的 `docker` 與 `docker compose` 指令，後續步驟不用改。

驗證（Docker 必須在執行中）：

```bash
docker --version
docker compose version
docker run hello-world
```

### 1-3. uv 與 Python 3.12

本專案鎖定 Python 3.12（與容器映像 `python:3.12-slim` 一致）。
Homebrew 的 `python3` 已是 3.15，**不要拿它當專案直譯器**，改由 uv 管理版本：

```bash
brew install uv
uv python install 3.12
```

驗證：

```bash
uv --version
uv python list | grep 3.12      # 應看到 cpython-3.12.x-macos-aarch64
uv run --python 3.12 python --version
```

之後在 `backend/`、`mcp-server/` 目錄各執行一次 `uv python pin 3.12`，產生 `.python-version`，`uv run` 就會自動用 3.12。

> macOS 內建沒有 `python` 指令，只有 `python3`。文件中凡是 `python ...` 一律用 `uv run python ...` 或 `python3 ...`。

### 1-4. Node.js LTS

```bash
brew install node
```

驗證：

```bash
node --version
npm --version
```

> Homebrew 的 `node` 是最新版（目前 26）。若要嚴格對齊容器用的 Node 22 LTS，可改 `brew install node@22` 並依提示加 PATH；本機開發用最新版即可。

### 1-5. macOS 設定（選用但建議）

- 第一次 `docker compose up` 或 `npm run dev` 時，macOS 防火牆若跳出「是否允許接收連入網路連線」，按允許。
- 在 `~/.zshrc` 加常用別名，少打幾個字：

```bash
alias dc='docker compose'
```

- 若用 iTerm2 或 cmux 等第三方終端機，確認 `claude` 指令可用：`which claude`。

## 完成條件

- [x] `brew --version` 正常
- [x] `docker run hello-world` 成功印出 Hello from Docker!
- [x] `uv --version` 正常
- [x] `uv run --python 3.12 python --version` 顯示 3.12.x
- [x] `node --version` 顯示 v22 或以上

## 下一步

→ [02-docker-postgres.md](02-docker-postgres.md)

## 實作紀錄

### 2026-11-02（Claude Code 檢查）

**已存在：**
- Homebrew 7.0.9、git 2.40.0、uv 0.11.25、node 26.12.0、npm 11.20.0 皆由 Homebrew 安裝，位於 `/opt/homebrew/bin`。
- Docker Desktop 已裝（`/Applications/Docker.app`，docker 29.8.2、compose v5.5.1），但檢查當下 daemon 未啟動。
- uv 已下載 cpython-3.12.13（`~/.local/share/uv/python/`），尚無任何專案 pin 到 3.12。

### 2026-11-02（晚間，完成）

- 手動開啟 Docker Desktop 後，`docker run hello-world` 成功（Server 29.8.2，aarch64）。
- 本步驟全部完成。建議到 Docker Desktop → Settings → General 勾選「Start Docker Desktop when you sign in」，否則重開機後要手動啟動。
