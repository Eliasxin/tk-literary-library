# 文學總站｜《四手聯彈，兩首奏鳴曲》與《八分音符》分層修正

## 本次正確的資料關係

- **總站原著分類**：四手聯彈，兩首奏鳴曲；英文顯示名稱 `Four Hands, Two Sonatas`。
- **原著分類下的個人作品**：八分音符；英文顯示名稱 `Quaver`；作品識別碼維持 `quaver`。
- Notion `原著分類` 填「四手聯彈，兩首奏鳴曲」，`系列名稱` 可以保留原本二創系列名稱，不需要改動識別碼。
- 如果 Notion 作品頁面目前仍叫 `Quaver`，請將**作品名**改成 `八分音符`，`英文顯示名稱` 保留 `Quaver`，同步後總站子作品才會顯示「八分音符 / Quaver」。不要修改 `作品識別碼`。

## 上傳檔案

覆蓋 `Eliasxin/tk-literary-library` 的 `main` 分支對應路徑：

1. `data/collections.json`：修正原著分類卡片的中文與英文顯示名，保留「四手聯彈」等 Notion 分類別名及五個綜合作品子分類。
2. `scripts/sync_notion_works.py`：保留既有同步程式，支援完整原著名稱與歷史別名。
3. `tests/test_works.py`：新增原著分類與個人作品分離的驗證測試。

**請勿覆蓋 `data/works.json` 與 `data/public-index.json`**，兩者是正式同步輸出。

上傳後先等 Cloudflare Pages 自動更新分類標題。若有在 Notion 改動作品名或勾選「總站顯示」，再手動執行 `Sync Notion Work Catalog`。未勾選的作品不會匯出，沒有公開文章也不會產生小說正文。
