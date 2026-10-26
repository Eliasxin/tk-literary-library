文學總資料庫：《戀習曲》未同步診斷版本

本更新包只包含 scripts/sync_notion_works.py
不要覆蓋 data/works.json、data/public-index.json 或其他已成功同步的資料。

操作：
1. 到 https://github.com/Eliasxin/tk-literary-library/edit/main/scripts/sync_notion_works.py
2. 將程式整份替換成此包裡 scripts/sync_notion_works.py 的內容，提交到 main。
3. 重新執行 Sync Notion Work Catalog。
4. 展開「Export opted-in Notion works」，找到「Catalog diagnostic / First Note of Love」幾行。

結果解讀：
- present in query: False = API 所查資料來源裡未包含識別碼為 first-note-of-love 的作品，應查資料來源/作品識別碼。
- present in query: True 且 display checkbox true: False = API 讀取的「總站顯示」不是已勾選，應查屬性類型/實際值。
- present in query: True 且 display checkbox true: True = 依目前程式應被匯出；若沒有，請回報日誌。

此版不會列出未授權作品名稱、Notion 頁面 ID、Token 或文章正文。
