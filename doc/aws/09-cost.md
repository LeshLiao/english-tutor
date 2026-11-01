# 09. 費用明細與各方案試算

查價日期：**2026-11-01**。區域以東京（ap-northeast-1）為主，單位美元，每月以 730 小時計。
台幣換算假設 1 USD = 32 TWD，僅供感覺用。上線前請用 https://calculator.aws 再算一次。

## 一、方案 A：Lightsail 單機（推薦起步）

| 項目 | 規格 | 單價 | 每月 |
|------|------|------|------|
| Lightsail 實例 | $12 方案：2 vCPU、2 GB、60 GB SSD、3 TB 流量、公開 IPv4 | $12 固定 | **$12.00** |
| 靜態 IP | 附加在實例上 | 免費（未附加才收 $0.005/小時） | $0 |
| 自動快照 | 約 10 GB 實際用量 × 7 天輪替 | $0.05/GB/月 | $0.50 |
| S3 備份 | 30 份 dump 合計 < 1 GB | $0.025/GB/月 | $0.03 |
| Route 53 hosted zone | 選用；用既有註冊商 DNS 則 $0 | $0.50/zone/月 | $0–0.50 |
| 流量超額 | 3 TB 內免費 | 超過 $0.09–0.14/GB | $0 |
| **合計** | | | **約 $13（NT$ 420）** |

**免費額度：**

- Lightsail 官方價格頁：Linux $5 / $7 / $12 方案，**新用戶前 3 個月免費**（每月 750 小時）。
- 2025-07-15 之後開的新帳號：註冊得 $100 抵用額，完成入門活動最多再 $100；Free plan 6 個月。
  $13 × 6 = $78 < $100，**前 6 個月實際上不用付錢**。第 6 個月前要升級 Paid plan，否則資源會被停掉。
- 抵用額是否能抵 Lightsail 以帳單為準；保守估計第一年總支出 $80–160。

**方案 A 一年：約 $80–160（含免費期）；之後每年約 $156（NT$ 5,000）。**

### 方案 A 長期開著會有什麼變動費用？

幾乎沒有。每月固定 $12 加零頭，會隨用量變動的只有下面這些，以這個專案的用量全部可忽略：

| 項目 | 免費額度 | 超過才收 | 這個專案預估 |
|------|----------|----------|--------------|
| 對外流量 | 每月 3 TB（$12 方案內含） | 東京約 $0.12–0.14/GB | MCP 請求與網頁幾 GB，不會超過 |
| 自動快照 | 無 | $0.05/GB/月，只算實際用量 | 磁碟用 5–10 GB，約 $0.25–0.50 |
| S3 備份 | 無 | $0.025/GB/月 | dump 合計 < 1 GB，約 $0.03 |
| Route 53 查詢 | 無 | $0.40/百萬次 | 用既有註冊商 DNS 則 $0 |

CPU 跑滿不會多收錢：$12 方案是 burstable 實例，CPU 點數用完只會被降速，不會產生額外帳單。

**會意外多出來的費用，都是「忘記」造成的：**

- **關機不等於停止計費。** Lightsail 實例只要存在就照月費算，Stop 也一樣；真的不用了要 Delete。
- **刪實例後的孤兒資源。** 靜態 IP 沒附加在實例上收 $0.005/小時（約 $3.65/月）；手動快照會一直留著。刪實例時要一起刪 IP 與快照。
- **免費額度到期。** 新帳號 6 個月免費方案結束、或 Lightsail 前 3 個月免費用完，就開始真的扣 $12（01-1 有提醒設月曆）。
- **不小心升級方案。** Lightsail 的 Change plan 只能往上不能往下，誤升到 $24 就回不來，只能從快照重建一台小的。

長期開著的實際帳單約每月 $12.5–13.5，不會因用量而明顯波動。
01-5 的 Budgets 門檻 $20 正常永遠不會觸發，一旦收到信就代表上面某個「忘記」發生了。

## 二、方案 A'：EC2 單機

| 項目 | 東京 t4g.small | 台北 t4g.small（ap-east-2） |
|------|----------------|------------------------------|
| 實例（2 vCPU ARM、2 GB） | $0.0216/小時 → $15.77 | $0.0194/小時 → $14.16 |
| EBS gp3 30 GB | $0.096/GB → $2.88 | 約 $2.88 |
| 公開 IPv4 | $0.005/小時 → $3.65 | $3.65 |
| EBS 快照 | 約 $0.50 | 約 $0.50 |
| Route 53 | $0–0.50 | $0–0.50 |
| **合計** | **約 $23（NT$ 740）** | **約 $21（NT$ 680）** |

比 Lightsail 貴 $8–10，換到的是台北區域（延遲 5–10 ms）、VPC 與正規 AWS 服務的銜接。
t4g 是 ARM，本機 Docker Desktop 要用 `--platform linux/arm64` 或在機器上 build。
x86 的 t3.small 東京約 $0.0272/小時（$19.9/月），比 t4g 貴 25%。

## 三、方案 B：Lightsail 實例 + Lightsail 託管資料庫

| 項目 | 每月 |
|------|------|
| Lightsail $12 實例（跑 backend、mcp、frontend、caddy） | $12.00 |
| Lightsail Managed Database Micro（PostgreSQL，1 vCPU、1 GB、40 GB、每日自動備份保留 7 天） | $15.00（新用戶第一個月免費） |
| 快照、S3、Route 53 | 約 $1.00 |
| **合計** | **約 $28（NT$ 900）** |

多花 $15 換到資料庫自動備份、一鍵還原、不用自己顧 Postgres 升級。
高可用版（兩個 AZ）$30，個人用不需要。

## 四、方案 C：ECS Fargate + RDS + ALB + S3/CloudFront

| 項目 | 規格 | 東京單價 | 每月 |
|------|------|----------|------|
| Fargate × 2 task（FastAPI、MCP） | 各 0.25 vCPU / 0.5 GB，全天 | 約 $0.0506/vCPU-hr + $0.0055/GB-hr（美東 $0.04048 + $0.004445） | $22.50 |
| Fargate task 公開 IPv4 × 2 | 放 public subnet 以免用 NAT Gateway | $0.005/小時 | $7.30 |
| RDS db.t4g.micro Single-AZ | 2 vCPU、1 GB | 約 $18（美東 $11.68） | $18.00 |
| RDS gp3 20 GB | | 約 $0.138/GB | $2.76 |
| RDS 自動備份 | 不超過資料庫大小免費 | | $0 |
| ALB | 固定費 | $0.0243/小時 | $17.74 |
| ALB LCU | 小流量 | $0.008/LCU-hr | $1.00 |
| ALB 公開 IPv4 × 2 AZ | ALB 最少跨 2 個 AZ | $0.005/小時 | $7.30 |
| Secrets Manager × 2 | DB 密碼、API key | $0.40/secret | $0.80 |
| ECR | 3 個映像約 1–3 GB | $0.10/GB | $0.30 |
| CloudWatch Logs | 約 1 GB/月 | 約 $0.76/GB 寫入 | $1.00 |
| S3 + CloudFront（前端） | CloudFront 永久免費 1 TB/月、1,000 萬請求 | | $0.10 |
| Route 53 | ALB alias 需要 Route 53 | $0.50 | $0.50 |
| ACM 憑證 | | 免費 | $0 |
| **合計** | | | **約 $80（NT$ 2,560），範圍 $75–95** |

**容易踩的費用陷阱：**

- **NAT Gateway**：Fargate 放 private subnet 要拉 ECR 映像就得有 NAT，東京 $0.062/小時 ≈ **$45/月**再加流量費。
  個人專案改放 public subnet + task 公開 IP（上表做法），或用 VPC endpoint（3 個 endpoint 約 $30/月，也不便宜）。
- **ALB 固定費 $25/月**不管有沒有流量；這是方案 C 與方案 A 差距的主因之一。
- **RDS Multi-AZ** 直接兩倍；個人用 Single-AZ 加自動備份即可。
- 用 Fargate Spot 可省 70%，但 MCP 長連線被中斷體驗不好，不建議。
- 2025-07 後的新帳號 Free plan 期間某些服務可能不開放或受限，要跑方案 C 建議直接升級 Paid plan。

## 五、方案 D：EKS

方案 C 的費用再加 EKS 控制平面 **$73/月**（$0.10/小時）與至少一台節點（t4g.medium 約 $31/月），
合計 $160 以上。Fargate profile for EKS 也可，但控制平面費跑不掉。只有要練 Kubernetes 才值得。

## 六、總表

| 方案 | 每月 | 每年 | 一句話 |
|------|------|------|--------|
| A. Lightsail 單機 | **$13** | $156（第一年 $80–160） | 最便宜、最快上線，與 Hostinger 同價位 |
| A'. EC2 單機 | $21–23 | $250–280 | 要台北區域或 VPC 才選 |
| B. Lightsail + 託管 DB | $28 | $336 | 多 $15 買資料庫安心 |
| C. Fargate + RDS + ALB | $80 | $960 | 正規架構，多人、高可用 |
| D. EKS | $160+ | $1,900+ | 練 K8s 才需要 |

對照：Hostinger KVM 1 促銷 $6.49/月（24 個月預付 $155.76），續約 $11.99/月；規格 1 vCPU / 4 GB / 50 GB，機房馬來西亞。
Lightsail $12 多一顆 vCPU、少 2 GB RAM、機房東京、不用預付兩年、有 AWS 生態。

## 七、查價來源

官方：

- Lightsail 價格頁：https://aws.amazon.com/lightsail/pricing/
- Lightsail 區域清單：https://docs.aws.amazon.com/lightsail/latest/userguide/understanding-regions-and-availability-zones-in-amazon-lightsail.html
- Lightsail 新增區域（2026-06）：https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-lightsail-aws-regions/
- Lightsail IPv4 收費說明：https://repost.aws/questions/QUbzlZML1ST-iAyxpFIw9mSg/lightsail-and-ipv4-address-costs
- 台北區域開放：https://aws.amazon.com/blogs/aws/now-open-aws-asia-pacific-taipei-region/
- ELB 價格頁：https://aws.amazon.com/elasticloadbalancing/pricing/
- 新制免費方案（$100–200 抵用額、6 個月）：https://builder.aws.com/content/3JW3kTH5S2UOzu1rvebQ1SDin34
- 公開 IPv4 收費：https://repost.aws/articles/ARknH_OR0cTvqoTfJrVGaB8A/why-am-i-seeing-charges-for-public-ipv4-addresses-when-i-am-under-the-aws-free-tier

第三方整理（價格以官方為準）：

- Lightsail 方案與免費 3 個月：https://cloudburn.io/blog/amazon-lightsail-pricing 、https://kuberns.com/blogs/aws-lightsail-pricing-your-comprehensive-guide/
- Lightsail 託管資料庫 $15：https://www.cloudzero.com/blog/amazon-lightsail-pricing/
- t4g.small 東京 $0.0216、t4g.micro $0.0108：https://www.economize.cloud/resources/aws/pricing/ec2/t4g.small/ 、https://instances.vantage.sh/aws/ec2/t4g.micro
- t4g.small 台北 $0.0194：https://cloudprice.net/aws/regions 、https://instances.vantage.sh/aws/ec2/t4g.small
- RDS db.t4g.micro 東京約 $18/月、美東 $11.68：https://www.bytebase.com/dbcost/rds/instance/db.t4g.micro/ 、https://infratally.com/articles/aws-rds-pricing-explained-2026/
- Fargate 美東 $0.04048 / $0.004445：https://www.cloudzero.com/blog/fargate-cost/ 、https://fortem.dev/blog/aws-fargate-pricing-real-costs/
- ALB 固定費與 LCU：https://cloudburn.io/blog/aws-elastic-load-balancing-pricing 、https://www.cloudzero.com/blog/aws-alb-pricing/
- EBS gp3 東京 $0.096：https://cloudchipr.com/blog/aws-ebs-pricing
- Route 53 $0.50/zone：https://www.stormit.cloud/blog/amazon-route-53-pricing/
- CloudFront 永久免費 1 TB：https://perfsys.com/blog/cloudfront-pricing-guide/
- 免費方案變更整理：https://infratally.com/articles/aws-free-tier-2026/ 、https://akalcloud.ai/blog/aws-free-tier-changes/
