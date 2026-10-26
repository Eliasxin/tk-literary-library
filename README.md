# SAKURAI_TK — The Literary Archive (14-collection edition)

The central library collects **14 parent categories**. Each parent can contain **multiple Notion works**, and each work can contain its own stories on an independent website.

## Data model (important)

1. **Parent category** — `data/collections.json` (14 top-level entries: Top Gun, 關於未知的我們, etc.). These are curated labels; no Notion page IDs or secrets.
2. **Individual work** — `data/works.json` generated from the existing Notion **📚 作品資料庫 / 我的作品**. Only rows with `總站顯示` checked are included. Works are grouped by `原著分類`; series/title fallback is supported for stand-alone categories.
3. **Published chapters** — `data/public-index.json` generated from the existing four public GitHub sites. No article body or unpublished draft is copied.

**Do not make duplicate Notion parent rows** just for the library. Keep existing works and chapter relations unchanged. Multiple works may use the same `總站排序`; they group by category, not by sort number.

## Install to GitHub and Cloudflare

Upload the entire package to a new repo, e.g. `Eliasxin/sakurai-literary-library`. Include both workflow files under hidden `.github/workflows/`.

Use Cloudflare Pages: select the repo, `main`, Framework preset `None`, no build command, output directory `.`. Deployments occur when GitHub commits change.

### Notion work metadata sync (NEW)

To connect the already-configured Notion works database, add two GitHub Actions **Repository Secrets** in the central library repository:

- `NOTION_TOKEN`: a read-enabled Notion Integration Token. Never put it in the repository or chat.
- `NOTION_WORKS_DATABASE_ID`: the 32-digit ID copied from your **works database** URL. **Not** the `章節資料庫` ID and **not** a database `v=` view ID.

Optional only when the database holds more than one data source:

- `NOTION_WORKS_DATA_SOURCE_ID`: the ID from Notion's "Manage data sources" menu. If there is exactly one source, the program discovers it automatically.

Authorize the same Integration to read the **works database**, then open `.github/workflows/sync-works.yml` under GitHub Actions → **Sync Notion Work Catalog** → **Run workflow**. The job uses Notion API version `2025-09-03` and reads the database's data-source ID before querying rows.

**Safe publishing**: A works row must explicitly have `總站顯示 = ☑` to appear as a subwork. `網站狀態 = 已上線` and a valid HTTPS `作品網站網址` are both required before it becomes a clickable subwork link. A row with `總站顯示` off is omitted entirely, including its name. The sync does not access the `📖 章節資料庫`, page blocks or article bodies.

This workflow schedules at approximately 11:00 Taiwan time (03:00 UTC), with manual runs available. GitHub may delay schedules. It writes only `data/works.json`.

### Public article title index (existing)

`.github/workflows/sync-index.yml` → **Sync Public Reading Index** → **Run workflow** to refresh published titles from the four public repositories, currently scheduled at approximately 11:30 Taiwan time (03:30 UTC):

- `Eliasxin/first-note-of-love`
- `Eliasxin/love-casting`
- `Eliasxin/top-gun-archive`
- `Eliasxin/unknown-archive`

The index stores **public titles, labels and valid deep links only**, not article bodies or tokens. It does not immediately run when individual site Actions run. If an article is unpublished, first run its source site's synchronization, and then refresh this central index. Always verify caches/CDN as necessary for urgent removals.

## Editing the 14 categories

`data/collections.json` defines category names, summaries, the verified series-site links, and `aliases` used by the Notion work grouper. It currently includes:

全面管控、夏日最後的秘密、路過我年少時光的藍色、對立而已、綜合作品、彈一場完美戀愛、關於未知的我們、戀愛 Casting、Heated Rivalry、JimmyOhm、RWRB、Top Gun、TopForm、療癒你的寵物（Healing Your Pet）。

If an opted-in Notion work uses a category name not present in this file, synchronization **fails explicitly** with a helpful mapping message rather than silently discarding it. Add an alias and rerun after checking the intended category.

Existing work identifiers remain unchanged; e.g. `first-note-of-love`, `the_distance_between_us`, and `unknown_shorts`.

## Verify locally

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
node --check app.js
python -m http.server 8000
```

Open `http://localhost:8000/` in a browser. The 14 categories show immediately. The subwork lists remain empty until you run the first GitHub Notion sync.
