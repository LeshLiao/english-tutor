# 從 Oregon $12 搬到 Tokyo $24（2026-11-07 實作紀錄）

## 目標

把 2026-11-02 部署在 Oregon 的 Lightsail $12 實例（2 GB）升級成 $24（4 GB），同時搬到離台灣近的東京區域。
程式碼、`.env`、資料庫全部靠快照帶過去，不重做 03/04。

## 為什麼

- 2 GB 跑五個容器已經很滿，再加桌面（[xfce-desktop.md](xfce-desktop.md)）或 build 會吃 swap。
- Lightsail 沒有原地升級，升級 = 從快照開新實例，既然要開新的就順便換區域。
- 東京到台灣約 35–50 ms，Oregon 約 130–160 ms；`/english-check` 與網頁操作會明顯變快。
- Lightsail 各區域同價，Tokyo $24 還是 $24。

## 步驟（實際做過）

1. **Oregon 拍手動快照**：實例頁 → Snapshots → Manual snapshots → 命名後 Create snapshot。
   不用停 Docker，快照是磁碟層級的 crash-consistent 複製，PostgreSQL 靠 WAL 自己復原。
2. **快照複製到東京**：快照右邊「⋮」→ Copy to another Region → Asia Pacific (Tokyo)。等幾分鐘。
3. **從複製的快照開新實例**：Console 區域切到 Tokyo → Snapshots → Create new instance。
   Zone A（ap-northeast-1a），Plan **$24**（2 vCPU / 4 GB / 80 GB / 4 TB），SSH key 沿用快照內設定。
4. **靜態 IP**：Networking → Create static IP → Tokyo → 附加到新實例。
   實例剛建好時拿到的是臨時 IP（13.231.235.105），附加靜態 IP 後變成 **35.79.82.165**。
   確認方式：實例頁 Networking 分頁，IP 旁邊標 Static IP 才算。
5. **防火牆**：新實例只有預設的 22/80，要手動加 HTTPS 443（IPv4 與 IPv6）。快照不會帶防火牆規則。
6. **本機設定改指新 IP**：
   - `~/.ssh/config` 的 `Host english-tutor` → `HostName 35.79.82.165`
   - english-tutor-plugin `.mcp.json` 的 `url` → `http://35.79.82.165/mcp`，版本 1.2.0 → 1.2.1，push 到 lesh-marketplace
   - 已安裝的 plugin 快取 `~/.claude/plugins/cache/lesh-marketplace/english-tutor-plugin/1.2.0/.mcp.json` 也直接改，重啟 Claude Code 即生效

## 驗證

從快照開機後容器會自己起來（`restart: unless-stopped`），不用手動 `up`：

```bash
# 機器上
hostname; free -h; df -h /                      # ip-172-26-6-190，3.7 GiB，77 GB
docker ps --format "table {{.Names}}\t{{.Status}}"   # 五個 Up，db/backend/mcp healthy
T=$(curl -s -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
curl -s -H "X-aws-ec2-metadata-token: $T" http://169.254.169.254/latest/meta-data/placement/availability-zone   # ap-northeast-1a

# Mac 上
curl -s -o /dev/null -w "%{http_code}\n" http://35.79.82.165/        # 200
curl -s -o /dev/null -w "%{http_code}\n" http://35.79.82.165/mcp     # 401（沒帶 key）
ssh english-tutor hostname                                            # ip-172-26-6-190
```

> 機器上 `cat /etc/machine-id` 與 Oregon 舊機器相同，這是從快照複製的正常現象，不影響運作。
> Lightsail metadata 要帶 IMDSv2 token，直接 curl 會回空字串。

## 結果

| 項目 | Oregon（舊） | Tokyo（新） |
|------|-------------|-------------|
| 區域 / Zone | us-west-2a | ap-northeast-1a |
| 方案 | $12（2 vCPU / 2 GB / 60 GB） | $24（2 vCPU / 4 GB / 80 GB） |
| 靜態 IP | 44.228.11.180 | 35.79.82.165 |
| 主機名 | ip-172-26-0-82 | ip-172-26-6-190 |
| Swap | 2 GB | 2 GB（跟著快照來） |

## 收尾（待做）

- [ ] Tokyo 防火牆加 443（IPv4 + IPv6）
- [ ] 重啟 Claude Code，`/english-tutor-plugin:english-check` 回歸測試通過
- [ ] 觀察幾天後刪 Oregon 實例 `Ubuntu-english-tutor`
- [ ] 釋放 Oregon 靜態 IP `english-tutor-ip`（沒附加的 IP 每月約 $3.65）
- [ ] 刪 Oregon 與 Tokyo 兩邊用不到的手動快照（每 GB 約 $0.05/月）
- [ ] 之後 05/07 的 S3、Route 53 等資源一律建在 ap-northeast-1
