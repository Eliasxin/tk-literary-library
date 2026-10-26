# 文學總站修正｜Quaver／綜合作品／名稱

這是 `Eliasxin/tk-literary-library` 的更新包，請將以下檔案覆蓋到 **main 分支的相同路徑**：

- `scripts/sync_notion_works.py`：修正 Notion「原著分類：四手聯彈」對應八分音符／Quaver；即使 `collections.json` 的分類別名漏更新也能容錯。保留勾選「總站顯示」才匯出的規則。
- `data/collections.json`：11 個頂層分類、綜合作品 5 個子分類，以及心機／Double Shuffle、八分音符／Quaver、Red, White & Royal Blue（標題不加 RWRB 縮寫）。
- `app.js`、`index.html`、`styles.css`：前端維持新的 11 個分類與綜合作品分組，RWRB 作為搜尋別名而非主標題。
- `tests/test_works.py`：19 項單元測試，涵蓋 Quaver、綜合作品五組、Notion 顯示勾選及資料隱私。

## 五個「綜合作品」子分類

1. 夏日最後的秘密
2. 路過我年少時光的藍色
3. 對立而已
4. JimmyOhm
5. TopForm

## 更新與測試

1. 上傳檔案後 Commit changes 到 GitHub `main` 分支。
2. 到 `.github/workflows/sync-works.yml` 手動執行 **Sync Notion Work Catalog**。
3. 展開 **Export opted-in Notion works**，確認已無 `ValueError: Quaver ... 四手聯彈`，並檢查「八分音符」及「綜合作品」的已收錄作品筆數。
4. 等 Cloudflare Pages 部署成功，確認《八分音符》、五個綜合作品子分類、心機英文名稱及 RWRB 顯示。

**注意：** 不要覆蓋或刪除 `data/works.json`、`data/public-index.json`；這份 ZIP 完全不包含它們，避免動到已索引的 117 篇公開文章。也不必修改任何原小說網站或 Notion Token。若 Notion 作品未勾選「總站顯示」，仍不會被匯出。

## 本機檢查

`python -m unittest discover -s tests -p 'test_*.py' -v`

已通過 19 項測試，JSON 格式與 Python 語法檢查也已通過；尚未替使用者執行正式 GitHub Actions 或線上同步。
