# SAKURAI_TK 文學總資料庫 V2｜完整部署說明

這是一份**完整可部署的靜態網站原始碼**。網站以「原著分類 → 作品 → 已公開篇名」三層架構呈現，14 個頂層分類由 `data/collections.json` 管理。

## 你的 Notion 資料庫

- **📚 作品資料庫 ID：** `3f59214c53e3806b9444fd55af430c2d`
- Notion 檢視 ID（網址 `v=` 後方）：`3f59214c53e380ce9d16000c5d30b9a8`，**不要填進 Secrets**。
- 舊「📖 章節資料庫」ID：`3f59214c53e3805f8153fab9b3367d2d`，**不要拿來替代作品資料庫 ID**。

## GitHub 一次上傳（全新儲存庫）

1. 開啟 `https://github.com/Eliasxin/sakurai-literary-library`。若尚未建立，先用 `https://github.com/new` 建立名稱 `sakurai-literary-library` 的儲存庫。
2. 解壓縮本 ZIP，將**裡面的檔案和資料夾**上傳到 GitHub 儲存庫根目錄，而不是把 ZIP 檔案上傳。
3. 務必檢查兩個隱藏路徑是否存在：
   - `.github/workflows/sync-works.yml`
   - `.github/workflows/sync-index.yml`
4. 確認以下 Python 程式存在：
   - `scripts/sync_notion_works.py`
   - `scripts/sync_public_catalog.py`
5. 提交到 `main` 分支。

**重要：** 如果這個 GitHub 專案已經上線並且完成過同步，不要用 ZIP 裡的初始 `data/works.json` 與 `data/public-index.json` 覆蓋現有生成資料；保留 GitHub 上的版本即可。第一次建立儲存庫時才需要上傳這兩個初始 JSON。

## GitHub Secrets（作品目錄同步）

`https://github.com/Eliasxin/sakurai-literary-library/settings/secrets/actions`

在 **Repository secrets** 設定：

- `NOTION_TOKEN`：此次文學總站 Notion Integration 的 Token（**不要放在程式碼、公開檔案或聊天**）。
- `NOTION_WORKS_DATABASE_ID`：`3f59214c53e3806b9444fd55af430c2d`

可選：

- `NOTION_WORKS_DATA_SOURCE_ID`：只有當同一個資料庫有**多個 Data Source** 才需設定；只有一個時可留空。

還要在 Notion「📚 作品資料庫」的 Connections（連接）中授權相同的 Integration。

## 兩個 GitHub Actions

### ① Sync Notion Work Catalog

`https://github.com/Eliasxin/sakurai-literary-library/actions/workflows/sync-works.yml`

讀取 Notion **作品資料庫**（不是章節資料庫），只匯出 `總站顯示` 已勾選的作品**中繼資料**到 `data/works.json`。

- 分類依「原著分類」與 `data/collections.json` 中的 `aliases` 判定。
- `網站狀態 = 已上線` 且 `作品網站網址` 為有效 HTTPS 時，才能點擊作品連結。
- 不讀取文章正文，不複製草稿內容，不修改原有四個獨立網站。
- 每日台灣時間上午約 11:00 執行（GitHub 排程可能延遲）；也可手動 Run workflow。

### ② Sync Public Reading Index

`https://github.com/Eliasxin/sakurai-literary-library/actions/workflows/sync-index.yml`

讀取四個既有公開 GitHub 站點的 `data/chapters.json`，建立 `data/public-index.json` 以搜尋已公開篇名。只匯入標題、分級/配對等公開中繼資料與閱讀連結，**不匯入小說正文**。

- 每日台灣時間上午約 11:30 執行（可能延遲）。
- 想讓剛發表的文章立即進總站搜尋：先完成來源站的 Notion Actions 同步與 Cloudflare 部署，再手動執行本工作流程。

## Cloudflare Pages 部署設定

- GitHub repository：`Eliasxin/sakurai-literary-library`
- Production branch：`main`
- Framework preset：`None`
- Build command：留空
- Build output directory：`.`（儲存庫根目錄）

## 14 個分類

全面管控、夏日最後的秘密、路過我年少時光的藍色、對立而已、綜合作品、彈一場完美戀愛、關於未知的我們、戀愛 Casting、Heated Rivalry、JimmyOhm、RWRB、Top Gun、TopForm、療癒你的寵物（Healing Your Pet）。

## 第一次同步可能發生的情況

- Actions 找不到工作流程：確認 `.github/workflows/*.yml` 真正位於 GitHub `main` 分支。
- `scripts/sync_notion_works.py` not found：代表 `scripts/` 漏傳。
- Notion HTTP 404：檢查資料庫 ID、Token 指向的 Integration，以及 Notion Connections 是否授權。
- Data Source 有多個：新增 `NOTION_WORKS_DATA_SOURCE_ID`。
- 分類對不上：先確認 Notion 的 `原著分類`，再視情況將相同名稱加到 `data/collections.json` 的 `aliases`。
- 部署後分類已出現、子作品仍空白：先執行「Sync Notion Work Catalog」，並確認各筆作品勾選「總站顯示」。

## 本機測試（選用）

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
node --check app.js
python -m http.server 8000
```

打開 `http://localhost:8000/`。
