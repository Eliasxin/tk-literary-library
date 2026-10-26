(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const state = { collections: [], works: [], chapters: [], synced: false, filter: 'all', shown: 24 };
  const text = value => String(value == null ? '' : value);
  const esc = value => text(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const searchText = value => text(value).normalize('NFKC').toLocaleLowerCase('zh-Hant');
  const safeLink = value => {
    if (typeof value !== 'string') return null;
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && url.hostname && !url.username && !url.password
        ? url.href : null;
    } catch (_) { return null; }
  };
  const kindLabel = work => ({original:'原創作品',fanfiction:'二次創作',translation:'翻譯作品',mixed:'綜合作品'}[work.type] || '作品分類');
  // Older published JSON may still contain the five former top-level category IDs.
  // Display those rows under 綜合作品 even before the next Notion sync completes.
  const miscSubcategoryIds = new Set(['summer-secret','blue-youth','opposites','jimmyohm','top-form']);
  const effectiveCollectionId = work => miscSubcategoryIds.has(work.collectionId) ? 'misc' : work.collectionId;
  const effectiveSubcategoryId = work => work.subcategoryId ||
    (miscSubcategoryIds.has(work.collectionId) ? work.collectionId : null);
  const listedFor = collection => state.works
    .filter(w => effectiveCollectionId(w) === collection.id)
    .sort((a,b) => (a.order ?? 999999) - (b.order ?? 999999) || a.title.localeCompare(b.title));

  function subworkUrl(work) {
    const base = safeLink(work.url);
    if (!base) return null;
    // Notion stores the root URL for both Unknown works. Link to the right section.
    if (work.collectionId === 'unknown' && work.id === 'the_distance_between_us')
      return base.split('#')[0] + '#series/serial';
    if (work.collectionId === 'unknown' && work.id === 'unknown_shorts')
      return base.split('#')[0] + '#series/shorts';
    if (work.collectionId === 'top-gun' && work.id === 'song_maketh_wingman')
      return base.split('#')[0] + '#series/song_maketh_wingman';
    if (work.collectionId === 'top-gun' && work.id === 'top_gun_random_writings')
      return base.split('#')[0] + '#series/top_gun_random_writings';
    return base;
  }

  function subworkHtml(work) {
    const url = subworkUrl(work);
    const published = work.status === 'online' && url;
    const name = `<strong>${esc(work.title)}</strong>${work.english && work.english !== work.title ? `<small>${esc(work.english)}</small>` : ''}`;
    return published
      ? `<a class="subwork-item" href="${esc(url)}" target="_blank" rel="noopener noreferrer"><span>${name}</span><span class="arrow" aria-hidden="true">↗</span></a>`
      : `<div class="subwork-item muted"><span>${name}</span><small>尚無公開連結</small></div>`;
  }

  function miscWorksHtml(collection, children) {
    // Named subcategories remain visible while the user is still preparing Notion rows.
    // No unpublished title, page body or page ID is exposed as a placeholder.
    const groupIds = new Set((collection.subcategories || []).map(g => g.id));
    const groups = (collection.subcategories || []).map(group => {
      const entries = children.filter(w => effectiveSubcategoryId(w) === group.id);
      return `<div class="misc-group">
        <div class="misc-group-heading"><strong>${esc(group.title)}</strong><span>${entries.length ? esc(String(entries.length)) + ' 部已收錄' : ''}</span></div>
        ${entries.length ? entries.map(subworkHtml).join('') : ''}
      </div>`;
    });
    const other = children.filter(w => !groupIds.has(effectiveSubcategoryId(w)));
    if (other.length) groups.push(`<div class="misc-group"><div class="misc-group-heading"><strong>其他綜合創作</strong><span>${other.length} 部已收錄</span></div>${other.map(subworkHtml).join('')}</div>`);
    return `<div class="work-sublist misc-sublist"><p class="work-sublist-title">綜合作品 / ${collection.subcategories?.length || 0} 個子分類</p>${groups.join('')}</div>`;
  }

  function workHtml(collection) {
    const children = listedFor(collection);
    const siteUrl = safeLink(collection.url);
    const online = collection.status === 'online' && siteUrl;
    const sublist = collection.id === 'misc'
      ? miscWorksHtml(collection, children)
      : children.length
        ? `<div class="work-sublist"><p class="work-sublist-title">收錄作品 / ${children.length}</p>${children.map(subworkHtml).join('')}</div>`
        : '';
    return `<article class="work-card accent-${esc(collection.accent || 'navy')} ${online ? '' : 'is-planned'}">
      <div class="work-top"><span class="work-number">${esc(collection.index)}</span><span class="work-state">${online ? '● 已有作品網站' : '○ 系列分類'}</span></div>
      <h3>${esc(collection.title)}</h3><p class="work-english">${esc(collection.english || '')}</p>
      <p class="work-copy">${esc(collection.summary || '')}</p>
      ${sublist}
      <div class="work-bottom"><span class="work-tag">${esc(kindLabel(collection))}</span>${online ? `<a class="work-action" href="${esc(siteUrl)}" target="_blank" rel="noopener noreferrer">前往系列網站 <span>↗</span></a>` : ''}</div>
    </article>`;
  }

  function renderWorks() {
    const term = searchText($('workSearch').value.trim());
    const matched = state.collections.filter(collection => {
      const matchFilter = state.filter === 'all' || (state.filter === 'planned'
        ? collection.status === 'planned' : collection.type === state.filter);
      const children = listedFor(collection);
      const hay = searchText([
        collection.title, collection.english, collection.summary,
        ...(collection.aliases || []),
        ...(collection.subcategories || []).flatMap(g => [g.title, g.english, ...(g.aliases || [])]),
        ...children.flatMap(w => [w.title, w.english])
      ].join(' '));
      return matchFilter && (!term || hay.includes(term));
    });
    $('workGrid').innerHTML = matched.length ? matched.map(workHtml).join('') : '<p class="empty">找不到符合條件的作品，請調整搜尋或分類。</p>';
  }

  function renderChapters() {
    const query = searchText($('chapterSearch').value.trim());
    const collection = $('chapterWork').value;
    if (!state.synced) {
      $('chapterCount').textContent = '公開篇章索引尚待首次同步';
      $('chapterList').innerHTML = '<p class="empty">作品書架可以先使用。執行總站的「Sync Public Reading Index」後，這裡會載入各網站已公開的篇名。</p>';
      return;
    }
    const matched = state.chapters.filter(ch => {
      const hay = searchText([ch.title, ch.subtitle, ch.workTitle, ch.section, ...(ch.cp || [])].join(' '));
      return (collection === 'all' || ch.workId === collection) && (!query || hay.includes(query));
    });
    $('chapterCount').textContent = `顯示 ${Math.min(matched.length, state.shown)} / ${matched.length} 篇公開文章 · 不包含正文`;
    if (!matched.length) {
      $('chapterList').innerHTML = '<p class="empty">目前沒有符合搜尋條件的公開篇章。</p>';
      return;
    }
    $('chapterList').innerHTML = matched.slice(0, state.shown).map(ch => {
      const url = safeLink(ch.readUrl);
      return `<article class="chapter-row">
        <div>${url ? `<a class="chapter-title" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(ch.title)} ↗</a>` : `<span class="chapter-title">${esc(ch.title)}</span>`}${ch.subtitle ? `<p class="chapter-subtitle">${esc(ch.subtitle)}</p>` : ''}</div>
        <span class="chapter-work">${esc(ch.workTitle)}${ch.section ? ' / ' + esc(ch.section) : ''}</span>
        <span class="chapter-cp">${esc((ch.cp || []).join('、') || '未標示 CP')}</span>
      </article>`;
    }).join('') + (matched.length > state.shown ? '<button class="load-more" id="loadMore" type="button">顯示更多篇章 ↓</button>' : '');
    $('loadMore')?.addEventListener('click', () => { state.shown += 24; renderChapters(); });
  }

  function fillWorksSelect() {
    const select = $('chapterWork');
    for (const collection of state.collections.filter(w => w.chaptersSource)) {
      const option = document.createElement('option');
      option.value = collection.id;
      option.textContent = collection.title;
      select.append(option);
    }
  }
  async function getJson(path) {
    const response = await fetch(path, {cache:'no-store'});
    if (!response.ok) throw new Error(`Cannot load ${path}: HTTP ${response.status}`);
    return response.json();
  }
  async function initialize() {
    try {
      const [catalog, workInfo] = await Promise.all([
        getJson('./data/collections.json'), getJson('./data/works.json')
      ]);
      if (!Array.isArray(catalog.collections) || !Array.isArray(workInfo.works)) {
        throw new Error('Invalid collection or works JSON');
      }
      state.collections = catalog.collections;
      state.works = workInfo.works;
      fillWorksSelect();
      renderWorks();
    } catch (error) {
      console.error('Works catalog load failed:', error);
      $('workGrid').innerHTML = '<p class="empty">暫時無法載入作品書架，請檢查總站 JSON 資料。</p>';
    }
    try {
      const info = await getJson('./data/public-index.json');
      state.synced = info.status === 'ready' && Array.isArray(info.chapters);
      state.chapters = state.synced ? info.chapters : [];
    } catch (error) {
      console.warn('Public reading index not available:', error);
    }
    renderChapters();
  }
  $('workSearch').addEventListener('input', renderWorks);
  for (const button of document.querySelectorAll('[data-filter]')) {
    button.addEventListener('click', () => {
      state.filter = button.dataset.filter;
      document.querySelectorAll('[data-filter]').forEach(b => {
        b.setAttribute('aria-pressed', String(b === button));
      });
      renderWorks();
    });
  }
  $('chapterSearch').addEventListener('input', () => { state.shown = 24; renderChapters(); });
  $('chapterWork').addEventListener('change', () => { state.shown = 24; renderChapters(); });
  initialize();
})();
