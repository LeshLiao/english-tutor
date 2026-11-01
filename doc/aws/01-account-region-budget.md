# 01. AWS 帳號檢查、區域與預算警報

## 目標

用既有的 AWS 帳號：確認 root 有 MFA、建立日常用的 IAM 使用者、確認區域用 Oregon、設好費用警報，確保不會莫名其妙被扣錢。

## 前置條件

- [總覽](00-README.md) 前置條件達成。
- 能以 root 登入既有的 AWS 帳號。

## 步驟

### 1-1. 既有帳號健檢

登入 Console 後花五分鐘確認：

- Billing → Payment methods：付款方式有效、未過期。
- Billing → Bills：看一下目前每月帳單，確認沒有忘記關的舊資源在扣錢；有的話先清掉，否則之後 Budgets 警報的門檻會算不準。
- Billing → Free Tier：若帳號還在免費額度期內會顯示剩餘量；本文件的費用估算一律以**正常付費價**計算，有額度就當作意外之喜。

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

### 1-4. 區域：Oregon（us-west-2）

這個帳號的其他專案都在 Oregon，為了集中管理，本專案也放 Oregon。

| 區域 | 代碼 | Lightsail | 台灣延遲 | 說明 |
|------|------|-----------|----------|------|
| **Oregon** | us-west-2 | 有 | 約 130–160 ms | **本專案用這個**：與其他專案同區；AWS 首發區域，服務最齊、價格最低 |
| 東京 | ap-northeast-1 | 有 | 約 35–50 ms | 延遲最好的替代；Lightsail 同價，其他服務貴約 20% |
| 台北 | ap-east-2 | **無** | 約 5–10 ms | 只有 EC2 等正規服務；走方案 A' 才用得到 |

延遲的實際影響：Hook 在背景執行感覺不到；手動 `/english-check` 與網頁操作每次請求多約 100 ms，可接受。
SSH 打字會有一點延遲，屬正常。

Console 右上角的區域選單切到 **US West (Oregon)**，之後每個服務（Lightsail、S3、IAM 以外）都要確認右上角是這一區。
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

- Receive CloudWatch billing alerts

### 1-6. 本機裝 AWS CLI（選用，07 會用到）

```bash
brew install awscli
aws --version
```

## 完成條件

- [ ] root 與 IAM 使用者皆啟用 MFA
- [ ] 日常以 IAM 使用者登入 Console
- [ ] Console 區域已切到 US West (Oregon)
- [ ] Budgets 兩條警報建立完成，收到建立確認信
- [ ] Bills 頁面確認沒有舊資源在扣錢

## 下一步

→ [02-lightsail-instance.md](02-lightsail-instance.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）
