# 文學總資料庫｜作品卡片文字精簡

這次只修改文字顯示，不更動 Notion API、作品 ID、分類對應或公開章節索引。

- `app.js`：移除作品卡片裡「此分類尚無已勾選『總站顯示』的作品，或尚未完成第一次 Notion 同步。」提示。沒有作品時保留分類卡片與簡介，不顯示系統空狀態。
- `app.js`：「綜合作品」的空子分類不再顯示「待收錄」，沒有系列網站的卡片不再顯示「尚未提供系列網站」的冗餘文字。
- `data/collections.json`：《四手聯彈，兩首奏鳴曲》的簡介正式改成「以《四手聯彈，兩首奏鳴曲》為原著的二次創作分類」。其他分類簡介完全保留。
- `index.html`：將 app.js 快取版本提高，方便部署後載入修正。

## 上傳

將三個檔案覆蓋至 `Eliasxin/tk-literary-library` 的 `main` 分支相同路徑：

- `app.js`
- `index.html`
- `data/collections.json`

請不要覆蓋 `data/works.json` 或 `data/public-index.json`，以保留既有的 Notion 已同步作品資料與公開篇章索引。

## 關於預計新增的 Notion「簡介」欄位

**本次尚不啟用此欄位**。等你新增欄位並提供內容後，再修改 `scripts/sync_notion_works.py` 與 `app.js`，讓網站適當讀取作者自己撰寫的簡介。這次其他簡介維持原樣，不會自動被覆蓋。
