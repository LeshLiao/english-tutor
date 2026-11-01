# 01. AWS 帳號、區域與預算警報

## 目標

開好 AWS 帳號、root 帳號上 MFA、建立日常用的 IAM 使用者、決定區域、設好費用警報，確保不會莫名其妙被扣錢。

## 前置條件

- [總覽](00-README.md) 前置條件達成。
- 一個專用的 email（建議開一個 `aws-english@...` 別名，不要用公司或共用信箱）。

## 步驟

### 1-1. 開帳號

- 到 https://aws.amazon.com/free 註冊。
- 2025-07-15 之後的新帳號採「抵用額制」免費方案：
  - 註冊即得 **$100** 抵用額，完成 5 項入門活動（各 $20）可再拿 **$100**，合計最多 $200。
  - 免費方案（Free plan）**6 個月**結束，或抵用額用完，兩者先到者為準；抵用額本身 12 個月到期。
  - Free plan 期間不會向信用卡扣款；但 6 個月到期時若沒升級成 Paid plan，資源會被停掉。
  - **請在月曆上記下「開戶日 + 5 個月」提醒自己升級 Paid plan**，不然資料庫會跟著消失。
- 2025-07-15 之前開的舊帳號維持舊制（12 個月固定用量免費），本文件不適用舊制細節。

### 1-2. root 帳號安全

- IAM → Security credentials → 為 root 啟用 MFA（手機 Authenticator app 即可）。
- 之後 root 只用來付款與極少數設定，日常操作用下一步的 IAM 使用者。

### 1-3. 日常用 IAM 使用者

最簡單的做法（個人專案）：

1. IAM → Users → Create user，名稱 `lesh-admin`，勾選 Console access。
2. 權限：Attach policies directly → `AdministratorAccess`。
3. 建立後登入一次，一樣啟用 MFA。
4. 若要在本機用 AWS CLI（07 備份會用到另一個權限更小的使用者，這裡先不用建 access key）。

> 正規做法是 IAM Identity Center（SSO），但個人一人用一個 IAM user 就夠。

### 1-4. 選區域

| 區域 | 代碼 | Lightsail | 台灣延遲 | 說明 |
|------|------|-----------|----------|------|
| **東京** | ap-northeast-1 | 有 | 約 35–50 ms | **預設選這個**：成熟、服務最齊、價格在亞洲屬中間 |
| 香港 | ap-east-1 | 有 | 約 20–35 ms | 需在帳號設定「opt-in」啟用；價格略高於東京 |
| 台北 | ap-east-2 | **無** | 約 5–10 ms | 2025 年開放，只有 EC2 等正規服務；走方案 A' 才用得到 |
| 新加坡 | ap-southeast-1 | 有 | 約 50–70 ms | 備選 |

Hook 在背景執行、MCP 呼叫是單次請求，30 ms 左右的差異感覺不到，選東京即可。
**區域一旦建了資源就不好搬**（要用快照複製），請在這一步決定。

### 1-5. 費用警報（一定要做）

**AWS Budgets**（Billing → Budgets → Create budget）：

| 欄位 | 值 |
|------|----|
| 類型 | Cost budget |
| 週期 | Monthly |
| 金額 | $20（方案 A 正常 $13 左右，超過代表有東西沒關） |
| 警報 1 | Actual ≥ 80%（$16）→ email |
| 警報 2 | Forecasted ≥ 100%（$20）→ email |

Cost budget 前兩個免費。

另外到 Billing → Billing preferences 勾選：

- Receive Free Tier usage alerts（抵用額快用完會通知）
- Receive CloudWatch billing alerts

### 1-6. 本機裝 AWS CLI（選用，07 會用到）

```powershell
winget install Amazon.AWSCLI
aws --version
```

## 完成條件

- [ ] root 與 IAM 使用者皆啟用 MFA
- [ ] 日常以 IAM 使用者登入 Console
- [ ] 已決定區域（預設東京）
- [ ] Budgets 兩條警報建立完成，收到建立確認信
- [ ] 月曆已記「開戶日 + 5 個月：升級 Paid plan」

## 下一步

→ [02-lightsail-instance.md](02-lightsail-instance.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）
