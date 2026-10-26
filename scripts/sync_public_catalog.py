#!/usr/bin/env python3
"""Index ONLY public, previously exported GitHub story metadata.

No Notion API and no Notion token. No blocks/body text is stored in the index.
Does not change any source site's data; each source site remains the reading host.
If any required source is unavailable or malformed, fail without changing the output.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data' / 'collections.json'
TARGET = ROOT / 'data' / 'public-index.json'
USER = 'Eliasxin'
SOURCE_REPOS: dict[str, str] = {
    'first-note': 'first-note-of-love',
    'love-casting': 'love-casting',
    'top-gun': 'top-gun-archive',
    'unknown': 'unknown-archive',
}
SLUG = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$')
BASE = 'https://raw.githubusercontent.com/'


def read_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={'User-Agent': 'SAKURAI-Literary-Catalog/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            if response.status != 200:
                raise RuntimeError(f'HTTP {response.status} for {url}')
            raw = response.read(12 * 1024 * 1024 + 1)
            if len(raw) > 12 * 1024 * 1024:
                raise RuntimeError(f'Source exceeds size limit: {url}')
            return json.loads(raw)
    except (urllib.error.URLError, json.JSONDecodeError) as error:
        raise RuntimeError(f'Cannot read public exported JSON from {url}: {error}') from None


def public_rows(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get('chapters'), list):
        rows = payload['chapters']
    else:
        raise ValueError('Expected a list of public chapters or {"chapters": [...]}')
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError('Malformed chapter collection')
    return rows


def is_visible(row: dict) -> bool:
    """Extra safety for exporters that happen to include an explicit visibility field."""
    if (row.get('isPublic') is False or row.get('websitePublic') is False
            or row.get('網站公開') is False or row.get('published') is False):
        return False
    status = row.get('status', row.get('發布狀態'))
    if status is not None:
        if isinstance(status, dict):
            status = status.get('name')
        if str(status).strip() not in ('已發布', '已發佈', 'published', 'Published'):
            return False
    return True


def make_url(work_id: str, row: dict, base_url: str) -> str | None:
    # First Note of Love uses its article `id`/`order` and opens its reader
    # in a JavaScript dialog. The current archived reader has no verified
    # chapter-specific URL: link to the working site rather than invent one.
    if work_id == 'first-note':
        return base_url
    slug = str(row.get('slug', '')).strip()
    if not SLUG.fullmatch(slug):
        return None
    slug = urllib.parse.quote(slug, safe='')
    if work_id == 'love-casting':
        return f'{base_url}#/read/{slug}'
    if work_id in ('top-gun', 'unknown'):
        section = str(row.get('work', '')).strip()
        if not SLUG.fullmatch(section):
            return None
        return f'{base_url}#read/{urllib.parse.quote(section, safe="")}/{slug}'
    return None


def normalize(source_id: str, work: dict, rows: list[dict]) -> list[dict]:
    result: list[dict] = []
    base_url = work['url']
    if not base_url.startswith('https://') or not base_url.endswith('.pages.dev/'):
        raise ValueError(f'Unsupported site URL for {source_id}')
    for row in rows:
        # The First Note site's own reader requires BOTH fields. Mirror that
        # exact rule so its drafts never enter the cross-site public index.
        if source_id == 'first-note' and not (
            row.get('published') is True and
            str(row.get('status', '')).strip() in ('已發布', '已發佈')
        ):
            continue
        if not is_visible(row):
            continue
        title = str(row.get('title') or '').strip()
        url = make_url(source_id, row, base_url)
        if not title or not url:
            continue
        pair = row.get('cp') or row.get('pairs') or []
        if isinstance(pair, str):
            pair = [pair]
        if not isinstance(pair, list):
            pair = []
        section = row.get('work', '')
        if source_id == 'unknown':
            section = {'serial': 'The Distance Between Us', 'shorts': '獨立短篇集'}.get(section, '')
        elif source_id == 'top-gun':
            section = {'song_maketh_wingman': 'Song Maketh Wingman',
                       'top_gun_random_writings': '隨寫系列'}.get(section, '')
        elif source_id == 'first-note':
            section = '戀習曲'
        else:
            section = ''
        result.append({
            'workId': work['id'],
            'workTitle': work['title'],
            'title': title[:250],
            'subtitle': str(row.get('subtitle') or '')[:250],
            'section': section,
            'cp': [str(c)[:100] for c in pair if isinstance(c, str)][:10],
            'readUrl': url,
        })
    return result


def build() -> dict:
    works_data = json.loads(SOURCE.read_text(encoding='utf-8'))
    works = {w['id']: w for w in works_data['collections'] if w.get('chaptersSource')}
    collected: list[dict] = []
    for work_id, repo in SOURCE_REPOS.items():
        if work_id not in works:
            raise ValueError(f'Missing {work_id} catalog entry')
        url = f'{BASE}{USER}/{repo}/main/data/chapters.json'
        rows = public_rows(read_json(url))
        normalized = normalize(work_id, works[work_id], rows)
        print(f'{work_id}: public JSON {len(rows)} records, indexed {len(normalized)} usable titles')
        collected.extend(normalized)
    collected.sort(key=lambda row: (row['workId'], row['title'].casefold()))
    old = None
    if TARGET.exists():
        try:
            old = json.loads(TARGET.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            pass
    new = {'updatedAt': dt.datetime.now(dt.timezone.utc).isoformat(), 'status': 'ready', 'chapters': collected}
    if isinstance(old, dict) and old.get('chapters') == collected and old.get('status') == 'ready':
        new['updatedAt'] = old.get('updatedAt')
    return new


def main() -> None:
    payload = build()  # Important: write only after all source repos have succeeded.
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
    if not TARGET.exists() or TARGET.read_text(encoding='utf-8') != rendered:
        TARGET.write_text(rendered, encoding='utf-8')
    print(f'Public story index: {len(payload["chapters"])} titles; no Notion credentials or article bodies copied.')


if __name__ == '__main__':
    main()
