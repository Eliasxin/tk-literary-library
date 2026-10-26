# 文學總站《戀習曲》文章索引修正

## 修改內容

這份修正只更新文學總站的公開篇章索引程式，不變更任何獨立網站或 Notion 資料。

- 《戀習曲》的 `data/chapters.json` 以 `id` / `order` 辨識作品，未必包含 `slug`；舊版索引程式要求 `slug`，導致篇名被跳過。
- 新版允許《戀習曲》已發布的文章使用現有格式進入文學總站索引。
- **保護草稿**：只收錄 `published == true` 且 `status == 已發布／已發佈` 的《戀習曲》文章。
- 索引僅包含作品標題、CP 與網址等公開中繼資料，**不複製小說正文**。
- 《戀習曲》既有閱讀器為對話框，未證實可直接透過 URL 打開單篇，因此先將篇名連結指向作品首頁，不使用無效的 `#/story/slug`。
- 其他三座網站的文章連結規則保持不變。

## 上傳至 GitHub

儲存庫：https://github.com/Eliasxin/tk-literary-library

1. 覆蓋 `scripts/sync_public_catalog.py`。
2. 覆蓋 `tests/test_catalog.py`（可選，但建議連同上傳）。
3. Commit changes 到 `main`。
4. 開啟 Actions：https://github.com/Eliasxin/tk-literary-library/actions/workflows/sync-index.yml
5. 選擇 **Run workflow**。
6. 展開 **Build public reading index**，確認日誌出現 `first-note: public JSON N records, indexed M usable titles`。
7. 如果 M>0，再檢查 `data/public-index.json` 的 `first-note` 相關紀錄，及 Cloudflare 網站的「公開篇章」搜尋。

如果 `first-note: ... indexed 0 usable titles`，表示正式來源資料可能和目前保留的原站版本不同。此時應提供該行日誌及公開 JSON 的欄位結構（不要貼出正文或 Token），再調整對應規則。

## 另一個獨立問題

`Sync Notion Work Catalog` 之前仍只匯出 7 筆作品，是 **作品目錄** 的資料來源問題；本修正只解決 **公開篇章索引**，不會直接改變 `data/works.json`。如果《戀習曲》仍未顯示成一筆子作品，需要繼續核對 `Catalog diagnostic / First Note of Love` 的幾行日誌。
