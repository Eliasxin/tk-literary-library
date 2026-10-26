#!/usr/bin/env python3
"""Read opted-in Notion work *metadata* to group catalog entries.

No chapter body, page blocks, drafts, tokens, or relation-linked page bodies are
exported. A row must explicitly have `總站顯示` checked to be indexed.

Notion API 2025-09-03: query a data source, not the enclosing database.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import urllib.error
import urllib.request
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
COLLECTIONS_PATH = ROOT / 'data' / 'collections.json'
OUTPUT_PATH = ROOT / 'data' / 'works.json'
API_ROOT = 'https://api.notion.com/v1'
NOTION_VERSION = '2025-09-03'
MAX_ROWS = 5000


def plain(prop: Any) -> str:
    if not isinstance(prop, dict):
        return ''
    kind = prop.get('type')
    if kind in ('rich_text', 'title'):
        return ''.join(fragment.get('plain_text', '') for fragment in prop.get(kind, []) if isinstance(fragment, dict)).strip()
    if kind in ('select', 'status'):
        record = prop.get(kind) or {}
        return str(record.get('name') or '').strip()
    if kind == 'formula':
        formula = prop.get('formula') or {}
        return str(formula.get('string') or '').strip()
    return ''


def checked(props: dict, name: str) -> bool:
    prop = props.get(name) or {}
    return prop.get('type') == 'checkbox' and prop.get('checkbox') is True


def order_value(props: dict) -> int:
    prop = props.get('總站排序') or {}
    value = prop.get('number') if prop.get('type') == 'number' else None
    return int(value) if isinstance(value, (int, float)) and value >= 0 else 999999


def allowed_link(props: dict) -> str | None:
    from urllib.parse import urlparse
    prop = props.get('作品網站網址') or {}
    value = prop.get('url') if prop.get('type') == 'url' else None
    if not isinstance(value, str):
        return None
    url = urlparse(value)
    # Reject non-HTTPS, URL embedded credentials, private/local domains.
    if (url.scheme != 'https' or not url.netloc or url.username or url.password
            or url.hostname in ('localhost', '127.0.0.1') or
            (url.hostname or '').endswith('.local')):
        return None
    return value


def key(value: str) -> str:
    import unicodedata
    value = unicodedata.normalize('NFKC', value).casefold()
    return ''.join(c for c in value if c.isalnum())


# 已確認的 Notion 原著分類與總站分類 ID。此處保留最重要的
# 相容性別名，避免只更新 Python、漏覆蓋 collections.json 時 Quaver 同步中斷。
# 顯示文字仍以 data/collections.json 為準，不會把私有草稿公開。
FIXED_CATEGORY_ALIASES = {
    'four-hands': (
        '四手聯彈', '四手联弹', '四手聯彈，兩首奏鳴曲',
        '四手聯彈、兩首奏鳴曲', '四手聯彈 兩首奏鳴曲',
        '四手聯彈：兩首奏鳴曲', '八分音符', 'Quaver',
        'Four Hands, Two Sonatas',
    ),
    'shin-ji': ('心機', '心机', 'Double Shuffle', 'SHIN JI: Double Shuffle'),
    'rwrb': ('RWRB', '王室緋聞守則', 'Red, White & Royal Blue'),
    'first-note': ('彈一場完美戀愛', '戀習曲', 'First Note of Love'),
}

FIXED_MISC_SUBCATEGORY_ALIASES = {
    'summer-secret': ('夏日最後的秘密', 'Summer Blue Hour'),
    'blue-youth': ('路過我年少時光的藍色', 'Blue Canvas of Youthful Days'),
    'opposites': ('對立而已', 'Fight for You'),
    'jimmyohm': ('JimmyOhm', 'Jimmy Ohm'),
    'top-form': ('TopForm', 'Top Form'),
}


def known_category(candidate: str, categories: list[dict]) -> str | None:
    normalized = key(candidate)
    available = {category.get('id') for category in categories}
    for category_id, aliases in FIXED_CATEGORY_ALIASES.items():
        if category_id in available and any(normalized == key(alias) for alias in aliases):
            return category_id
    return None


def misc_subcategory(props: dict, categories: list[dict]) -> str | None:
    """Resolve formerly top-level labels under 綜合作品 without changing Notion relations.

    Never export a subgroup name or title from a private/unchecked Notion page.
    """
    misc = next((category for category in categories if category['id'] == 'misc'), None)
    if misc is None:
        return None
    alias_to_id: dict[str, str] = {}
    for subgroup in misc.get('subcategories', []):
        for alias in [subgroup['title'], subgroup['id'], *(subgroup.get('aliases') or [])]:
            alias_to_id[key(alias)] = subgroup['id']
    # 兼容舊版 collections.json 的分類別名，且只對存在的子分類生效。
    enabled = {subgroup.get('id') for subgroup in misc.get('subcategories', [])}
    for subgroup_id, aliases in FIXED_MISC_SUBCATEGORY_ALIASES.items():
        if subgroup_id in enabled:
            for alias in aliases:
                alias_to_id[key(alias)] = subgroup_id
    # Original / series are more reliable than a title that resembles a category.
    for candidate in (plain(props.get('原著分類')), plain(props.get('系列名稱')), plain(props.get('作品名'))):
        if key(candidate) in alias_to_id:
            return alias_to_id[key(candidate)]
    return None


def category_for(props: dict, categories: list[dict]) -> str:
    """Group designated mixed works under 綜合作品; otherwise prefer 原著分類."""
    if misc_subcategory(props, categories):
        return 'misc'
    alias_to_id: dict[str, str] = {}
    for category in categories:
        for alias in [category['title'], category['id'], *(category.get('aliases') or [])]:
            alias_to_id[key(alias)] = category['id']
    original = plain(props.get('原著分類'))
    series = plain(props.get('系列名稱'))
    title = plain(props.get('作品名'))
    for candidate in (original, series, title):
        if key(candidate) in alias_to_id:
            return alias_to_id[key(candidate)]
        fallback = known_category(candidate, categories)
        if fallback:
            return fallback
    # Avoid silently hiding new, explicitly opted-in works.
    raise ValueError(f'已勾選總站顯示的作品「{title}」無法判斷原著分類：{original or "(空白)"}。請先在 data/collections.json 設定分類別名。')


def to_work(page: dict, categories: list[dict]) -> dict | None:
    props = page.get('properties') or {}
    if not checked(props, '總站顯示'):
        return None
    title = plain(props.get('作品名'))
    slug = plain(props.get('作品識別碼'))
    if not title or not slug:
        raise ValueError('有已勾選「總站顯示」的作品未設定作品名或作品識別碼。')
    if len(title) > 200 or len(slug) > 150:
        raise ValueError('作品名稱或識別碼超過允許長度。')
    url = allowed_link(props)
    online_flag = plain(props.get('網站狀態')) == '已上線'
    collection_id = category_for(props, categories)
    record = {
        'id': slug,
        'collectionId': collection_id,
        'title': title,
        'english': plain(props.get('英文顯示名稱'))[:200],
        'status': 'online' if online_flag and url else 'planned',
        'url': url if online_flag else None,
        'order': order_value(props),
    }
    # Only include this extra public label for explicitly opted-in mixed works.
    if collection_id == 'misc':
        subcategory = misc_subcategory(props, categories)
        if subcategory:
            record['subcategoryId'] = subcategory
    return record


def build_works(pages: list[dict], categories: list[dict]) -> list[dict]:
    result: list[dict] = []
    seen: set[str] = set()
    for page in pages:
        entry = to_work(page, categories)
        if entry is None:
            continue
        if entry['id'] in seen:
            raise ValueError(f'重複作品識別碼：{entry["id"]}。請先調整 Notion。')
        seen.add(entry['id'])
        result.append(entry)
    indexes = {cat['id']: int(cat['index']) for cat in categories}
    result.sort(key=lambda w: (indexes[w['collectionId']], w['order'], w['title']))
    return result


def notion_call(path: str, token: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode('utf-8') if payload is not None else None
    request = urllib.request.Request(
        API_ROOT + path,
        data=body,
        method='POST' if payload is not None else 'GET',
        headers={
            'Authorization': 'Bearer ' + token,
            'Notion-Version': NOTION_VERSION,
            'Content-Type': 'application/json',
            'User-Agent': 'SAKURAI-Literary-Catalog/2.0',
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f'Notion API HTTP {error.code} at {path.split("/")[1]} endpoint. '
            'Check database ID, Integration permissions and GitHub Secrets.'
        ) from None


def get_pages(token: str, database_id: str, explicit_source_id: str = '') -> list[dict]:
    database = notion_call('/databases/' + database_id, token)
    available = [source.get('id') for source in database.get('data_sources', [])]
    if not available:
        raise RuntimeError('此 Notion 資料庫沒有可用的 data source。')
    if explicit_source_id:
        if explicit_source_id not in available:
            raise RuntimeError('NOTION_WORKS_DATA_SOURCE_ID 不屬於指定資料庫。')
        source_id = explicit_source_id
    elif len(available) == 1:
        source_id = available[0]
    else:
        raise RuntimeError('資料庫有多個 data sources，請設定 NOTION_WORKS_DATA_SOURCE_ID。')
    rows: list[dict] = []
    cursor = None
    while True:
        payload: dict = {'page_size': 100}
        if cursor:
            payload['start_cursor'] = cursor
        result = notion_call('/data_sources/' + source_id + '/query', token, payload)
        rows.extend(result.get('results', []))
        if len(rows) > MAX_ROWS:
            raise RuntimeError('作品資料庫超過安全的最大筆數限制。')
        if not result.get('has_more'):
            break
        cursor = result.get('next_cursor')
        if not cursor:
            raise RuntimeError('Notion pagination cursor missing.')
    return rows



def diagnostic_first_note(pages: list[dict], records: list[dict]) -> None:
    """Diagnose one user-approved, already-public work without exposing private records.

    Print only presence and checkbox status for the known public catalog work.
    Never print page IDs, tokens, unchecked row names, or their metadata.
    """
    expected_slug = 'first-note-of-love'
    matches = [
        page for page in pages
        if plain((page.get('properties') or {}).get('作品識別碼')) == expected_slug
    ]
    print(f'Catalog diagnostic / First Note of Love / present in query: {bool(matches)}')
    if matches:
        props = matches[0].get('properties') or {}
        setting = props.get('總站顯示') or {}
        print(f'Catalog diagnostic / First Note of Love / display property exists: {"總站顯示" in props}')
        print(f'Catalog diagnostic / First Note of Love / display property is checkbox: {setting.get("type") == "checkbox"}')
        print(f'Catalog diagnostic / First Note of Love / display checkbox true: {checked(props, "總站顯示")}')
    print(f'Catalog diagnostic / First Note of Love / exported: {any(work["id"] == expected_slug for work in records)}')
    print(f'Catalog diagnostic / total records not opted in: {sum(not checked(page.get("properties") or {}, "總站顯示") for page in pages)}')


def main() -> None:
    token = os.environ.get('NOTION_TOKEN', '').strip()
    database_id = os.environ.get('NOTION_WORKS_DATABASE_ID', '').strip().replace('-', '')
    data_source_id = os.environ.get('NOTION_WORKS_DATA_SOURCE_ID', '').strip().replace('-', '')
    if not token or not re.fullmatch(r'[0-9a-fA-F]{32}', database_id):
        raise RuntimeError('請在 GitHub Secrets 設定 NOTION_TOKEN 與 NOTION_WORKS_DATABASE_ID（32 位資料庫 ID）。')
    catalog = json.loads(COLLECTIONS_PATH.read_text(encoding='utf-8'))
    categories = catalog['collections']
    pages = get_pages(token, database_id, data_source_id)
    records = build_works(pages, categories)
    diagnostic_first_note(pages, records)
    prior = None
    if OUTPUT_PATH.exists():
        try:
            prior = json.loads(OUTPUT_PATH.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            pass
    update_time = dt.datetime.now(dt.timezone.utc).isoformat()
    if isinstance(prior, dict) and prior.get('status') == 'ready' and prior.get('works') == records:
        update_time = prior.get('updatedAt') or update_time
    output = {'status': 'ready', 'updatedAt': update_time, 'works': records}
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Notion work records examined: {len(pages)}')
    print(f'Opted-in works exported: {len(records)}')
    for category in categories:
        count = sum(work['collectionId'] == category['id'] for work in records)
        if count:
            print(f'  {category["title"]}: {count} works')
    print('No article bodies, unpublished work metadata, tokens or Notion page IDs exported.')


if __name__ == '__main__':
    main()
