# Port Allocation — fleet SoT

> 一張表管所有產品的 port,別讓它住在腦袋裡。配 `docs/spine-modules.md`(#6 deploy)。
> 餵得進部署管理頁(`/ports`)。

## 規矩(Peter 定 2026-06-29)

- **前端 = `3` 開頭** · **後端/API = `8` 開頭** · **資料庫 = `5` 開頭**
- **每個產品一個編號 `NN`,三個埠共用同 NN** → 一看 `3001 / 8001 / 5401` 就知道是同一個產品(01)。
  - web = `30NN` · api = `80NN` · db = `54NN`(避開 native postgres 預設 5432)
  - aux(redis/minio/AI 等):盡量也帶 NN(redis `63NN`、AI `84NN`),不強制
- **保留**:`3000/8000` = rivendell dashboard(hub,NN=00);系統佔用 `5000/7000`(macOS AirPlay)、`5432`(native postgres)別碰。

## 配置表(current → target)

| NN | 產品 | web 30NN | api 80NN | db 54NN | aux | 現況 / 狀態 |
|----|------|---------|---------|--------|-----|------------|
| 00 | **rivendell** dashboard | 3000 | 8000 | — | — | ✅ 跑在 3000/8000(hub,保留) |
| 01 | chimesflow | 3001 | 8001 | 5401 | — | db 跑 **5434** → 待遷 |
| 02 | family-fiscal | 3002 | 8002 | 5402 | — | 跑 **3020/8020** → 待遷 |
| 03 | mops_dbs | 3003 | **8030-8039**(多服務) | 5403 | — | 跑 5441 / 808x → 待遷 |
| 04 | tukey-or | 3004 | 8004 | 5404 | — | 跑 **8011/5435** → 待遷 |
| 05 | **tukey-automl** | 3005 | 8005 | 5405 | redis 6305, minio 9005/9006 | ✅ **已改(本次)**,原 3000/8000/5432 元兇 |
| 06 | pti-ares | 3006 | 8006 | 5406 | — | db 跑 **5436** → 待遷 |
| 07 | ic-yms | 3007 | 8007 | 5407 | — | 尚未起,直接用此組 |
| 08 | iihi(孕) | 3008 | 8008 | 5408 | AI 8408 | 跑 **3300/8300/8400/5437** → 待遷 |
| 09 | sales-assistant | — | — | — | — | **已棄**,退役釋出 5433 |
| 10 | tukey-bi | 3010 | 8010 | 5410 | — | |
| 11 | tukey-etl | 3011 | 8011 | 5411 | — | 8011 待 tukey-or 遷走後釋出 |
| 12 | tukey-km | 3012 | 8012 | 5412 | — | |
| 13 | Edict | 3013 | 8013 | 5413 | — | 現用 7891 → 待遷 |
| 14 | news_stock | 3014 | 8014 | 5414 | — | |
| 15 | taiwan-company | 3015 | 8015 | 5415 | — | |

## 遷移政策(重要)

- **不 big-bang renumber 跑著的 prod**。改 db host port 要連動 `DATABASE_URL` + 重啟,風險 > 收益。
- **遷移時機 = 下次本來就要碰那個產品時**(redeploy / 改 compose)順手改成 target,改完更新本表狀態欄。
- **新產品(ic-yms…)直接用 target**,不要再隨手抓 3000/8000/5432。
- compose 只改 **host port(左邊)**;container port(右邊)+ 服務間用 service name(`db:5432`)+ 內部 healthcheck **不動**。改 web 的 host api port 記得同步 `NEXT_PUBLIC_API_URL`(瀏覽器打 host port,baked 進 bundle)。

## 本次已做

- ✅ tukey-automl(NN=05):`docker-compose.yml` host port `3000→3005 / 8000→8005 / 5432→5405 / 6379→6305 / 9000→9005 / 9001→9006`,`NEXT_PUBLIC_API_URL→:8005`。解掉與 rivendell dashboard(3000/8000)+ native postgres(5432)的三個衝突(它本來沒在跑,純改檔零風險)。
