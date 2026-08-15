# 反證操作手冊（Phase 2）

地圖上的每條邊都只是假說。這裡是把假說變成事實的具體操作。

**通則：先寫預測，再做實驗。** 不先寫下「我認為拔掉它會壞在哪」，
你會事後合理化任何結果，實驗就白做了。

---

## 1. 拔依賴

### 拔資料庫

```bash
# Docker Compose
docker compose stop postgres        # 或 db / mysql

# launchd (macOS，本機服務)
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/<label>.plist
# 復原：launchctl bootstrap gui/$(id -u) <plist>   ← 不要用 kill，會跟 respawn 打架

# 不想停服務就把連線字串改壞（最乾淨，影響範圍最小）
DATABASE_URL=postgresql://nobody@127.0.0.1:1/none <啟動指令>
```

跑一次主要旅程。**畫面照樣出得來 = DB 不在這條路徑上**，不管文件怎麼寫。

### 拔檔案 / 產物

```bash
mv work/pcb-enriched.json work/pcb-enriched.json.bak   # rename 不要 delete，要能復原
```

比刪除好的地方：出錯時看得到「找不到檔案」的錯誤訊息，能確認它真的被讀了。

### 反向：打開沒在用的路徑

有實作、預設關著、零測試的路徑（`STORAGE_BACKEND=minio` 而 env 一直是 `local`），
最有價值的實驗是**跑它一次**。兩段做，中間的差別就是結論：

```bash
# ① 服務沒起時先跑一次 —— 看它是明著爆，還是靜默 fallback 到別條路
STORAGE_BACKEND=minio ./.venv/bin/python -c "from app.storage import MinioStorage; MinioStorage()"
#   連線錯誤 = ✅ 不會假裝成功；沒報錯 = ❌ 有隱藏 fallback，正式切過去會以為在用 A 其實在用 B

# ② 起服務再跑一次完整 round-trip —— put → get → exists(命中) → exists(未命中)
docker compose up -d minio
```

**復原是實驗的一部分**：刪掉 probe 寫進去的物件、`docker compose rm -f <svc>` 移除臨時容器、
確認 `git status` 乾淨。報告裡寫明「已復原」，別讓讀的人替你擔心。

### 拔外部服務

改 host 指向黑洞（`127.0.0.1:1`）比斷網好 —— 斷網會同時拔掉一堆東西，
分不出是哪一條邊在起作用。

### 記錄格式

| store／服務 | 預測會壞的出口 | 實際 | 判讀 |
|---|---|---|---|
| postgres | 違規列表、判定頁 | 兩者都正常出 | ❌ 邊是假的 —— 違規列實際來自 `violations.json` |
| `work/geometry/*.arrow.zst` | 板圖 | 板圖空白 | ✅ 邊是真的 |

---

## 2. 旗標盤點

```bash
# 找旗標
rg -n 'os\.environ\.get\(|os\.getenv\(|process\.env\.|std::env::var\(' --glob '!node_modules'

# 找「執行中的行程」實際拿到什麼值（跟 .env 檔不一定一樣）
ps eww -p <pid> | tr ' ' '\n' | grep -i '<FLAG_NAME>'
launchctl print gui/$(id -u)/<label> | grep -A20 environment   # launchd 管的服務
```

**注意讀值的地方不只一處**：pydantic-settings 的 `env_file=` 只填 Settings 物件，
旁邊用 `os.environ.get()` 的程式碼看不到那個值 —— 同一個旗標可能在兩處讀到不同結果。

記錄格式：

```
名稱 | 預設值 | 預設走哪條路 | 另一條有沒有測試 | 上次翻過是什麼時候
PTI_READ_FROM_PG | false | 讀 violations.json | 有（parity test）| 未知
```

---

## 3. 壞資料閘門

造測試輸入，看是**明說不支援**還是**盡力而為**：

```bash
: > empty.tgz                                  # 空檔
head -c 1024 good.tgz > truncated.tgz          # 半截檔
printf 'not an archive' > garbage.tgz          # 型別錯
# 版本不認得：改 payload 裡的 schema_version 成 999
```

判讀標準：

| 行為 | 判讀 |
|---|---|
| 明確錯誤訊息 + 擋在畫面之前 | ✅ |
| 錯誤訊息含糊但有擋 | ⚠️ 記進報告 |
| **部分成功，畫面照出** | ❌ 最惡劣 —— 半套資料長得跟完整資料一樣 |

順帶記下**錯誤把使用者送去哪個畫面**：能改就重送的留在表單，
要處理的是別的物件就送回列表。錯誤訊息不只是文字，它決定下一步在哪。

---

## 4. 被吞掉的失敗

```bash
bash scripts/seam-scan.sh . --section failure
```

逐條問：**這裡失敗時，使用者看得到嗎？** 三種結果：

- 看得到（拋出去、進 UI）→ 正常
- 只進 log → 記進報告；如果吞掉的是「寫入 SoR」，那它就不是 SoR
- 連 log 都沒有 → 高優先，寫進報告第一段

---

## 5. 執行期追蹤（讀碼真的看不出來時）

讀碼與拔依賴都不夠時（動態 import、外掛式 handler、大量條件分支），直接看它跑時碰了什麼：

```bash
# macOS — 這個行程實際開了哪些檔（sudo 必要）
sudo fs_usage -w -f filesystem -p <pid> | grep -v '\.dylib'

# Linux
strace -f -e trace=openat -p <pid>

# 資料庫真的收到什麼（比讀 ORM 準）
# postgresql.conf: log_statement = 'all'  → 跑一次旅程 → 讀 log
```

成本高，留給前面手法都問不出答案的情況。

---

## 6. 復原檢查

反證是刻意破壞，做完一定要復原並確認回到原狀：

```bash
git status                # 有沒有留下改動
ls *.bak                  # rename 過的檔案復原了嗎
docker compose ps         # 服務起回來了嗎
```

**不要用 `git clean -fd` 復原** —— 會刪掉不屬於這次實驗的未追蹤檔案。
用 `git checkout -- .` 加手動處理 rename 過的檔案。
