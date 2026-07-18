/* BIU - Search Panel Functions */
// ---- 搜索状态 ----
let _searchTimer = null;
let _searchPage = 1;
let _searchKeyword = "";
let _searchHasMore = false;
let _searchAborter = null; // AbortController

function toggleSearchClear() {
  const input = $("header-search");
  const btn = $("search-clear");
  if (input.value.trim()) {
    btn.classList.add("visible");
  } else {
    btn.classList.remove("visible");
  }
  // 防抖触发 B 站搜索
  clearTimeout(_searchTimer);
  _searchTimer = setTimeout(() => performSearch(), 250);
}

function clearSearch() {
  const input = $("header-search");
  input.value = "";
  input.focus();
  toggleSearchClear();
  hideSearchPanel();
}

function onSearchKeydown(e) {
  if (e.key === "Escape") {
    clearSearch();
    e.target.blur();
  } else if (e.key === "Enter") {
    // 手动触发搜索（跳过防抖）
    clearTimeout(_searchTimer);
    performSearch();
  }
}

async function performSearch() {
  const q = $("header-search").value.trim();
  if (!q) {
    hideSearchPanel();
    return;
  }

  // 如果关键词变了，重置页码
  if (q !== _searchKeyword) {
    _searchKeyword = q;
    _searchPage = 1;
    _searchHasMore = false;
  }

  // 取消上一次请求
  if (_searchAborter) _searchAborter.abort();
  const aborter = new AbortController();
  _searchAborter = aborter;

  const isFirstPage = _searchPage === 1;
  if (isFirstPage) {
    showSearchPanel("loading");
  } else {
    // 加载更多时不清空已有结果，只显示底部加载中
    $("sp-more").textContent = "加载中...";
  }

  try {
    const resp = await fetch(
      `/api/search?q=${encodeURIComponent(q)}&page=${_searchPage}`,
      { signal: aborter.signal }
    );
    if (!resp.ok) throw new Error("search failed");
    const data = await resp.json();
    renderSearchResults(data.items, data.has_more, data.total);
  } catch (e) {
    if (e.name !== "AbortError") {
      if (isFirstPage) {
        showSearchPanel("error");
      } else {
        // 加载更多失败时恢复按钮
        $("sp-more").innerHTML = `<span onclick="loadMoreSearchResults()" style="cursor:pointer;color:var(--error)">加载失败，点击重试</span>`;
      }
    }
  }
  _searchAborter = null;
}

function showSearchPanel(state) {
  const panel = $("search-panel");
  const loading = $("sp-loading");
  const noResults = $("sp-no-results");
  const items = $("sp-items");
  const more = $("sp-more");

  panel.classList.add("show");
  $("search-backdrop").style.display = "block";
  loading.classList.toggle("show", state === "loading");
  noResults.classList.toggle("show", state === "error" || state === "empty");

  if (state === "loading" || state === "error") {
    items.innerHTML = "";
    more.style.display = "none";
  }
}

function hideSearchPanel() {
  const panel = $("search-panel");
  panel.classList.remove("show");
  $("search-backdrop").style.display = "none";
  _searchKeyword = "";
  _searchPage = 1;
  $("sp-items").innerHTML = "";
  $("sp-more").style.display = "none";
}

function renderSearchResults(items, hasMore, total) {
  const panel = $("search-panel");
  const loading = $("sp-loading");
  const noResults = $("sp-no-results");
  const itemsEl = $("sp-items");
  const more = $("sp-more");

  panel.classList.add("show");
  loading.classList.remove("show");

  if (!items || items.length === 0) {
    noResults.classList.add("show");
    itemsEl.innerHTML = "";
    more.style.display = "none";
    return;
  }

  noResults.classList.remove("show");
  _searchHasMore = hasMore;

  let html = "";
  items.forEach((v, i) => {
    // 封面：B站封面地址，用 @160w_100h 缩小
    const cover = v.cover ? v.cover.replace(/https?:/, "") + "@88w_56h" : "";
    const playCount = v.play ? formatPlayCount(v.play) : "";
    html += `<div class="sp-item" title="${esc(v.title)}" onclick="playSearchResult('${esc(v.bvid)}', '${esc(v.title)}', '${esc(v.author)}', ${v.duration_sec || 0})">
      ${cover ? `<img class="sp-cover" src="${cover}" alt="" loading="lazy">` : `<span class="sp-cover"></span>`}
      <div class="sp-info">
        <div class="sp-title">${esc(v.title)}</div>
        <div class="sp-meta-line">
          <span class="sp-author">${esc(v.author)}</span>
          ${playCount ? `<span class="sp-play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg> ${playCount}</span>` : ""}
        </div>
      </div>
      <span class="sp-dur">${esc(v.duration)}</span>
    </div>`;
  });

  if (_searchPage === 1) {
    itemsEl.innerHTML = html;
  } else {
    itemsEl.innerHTML += html;
  }

  more.innerHTML = '<span class="sp-more-arrow"></span>加载更多';
  more.onclick = function() { loadMoreSearchResults(); };
  more.style.display = hasMore ? "flex" : "none";
}

function loadMoreSearchResults() {
  if (!_searchHasMore) return;
  _searchPage++;
  performSearch();
}

function playSearchResult(bvid, title, author, duration) {
  hideSearchPanel();
  $("header-search").value = "";
  toggleSearchClear();

  // 直接播放搜索结果（不走收藏夹播放队列）
  currentFolder = null;
  playbackFolder = null;
  currentIndex = -1;
  playBvidSong(bvid, title, "", author, duration);
}

function formatPlayCount(n) {
  if (!n || n < 0) return "";
  if (n >= 10000) return (n / 10000).toFixed(1).replace(/\.0$/, "") + "万";
  return String(n);
}

function filterSongsInFolder(mediaId, q) {
  const data = folderContents[mediaId];
  if (!data) return 0;

  const container = $$(`.folder-content[data-mid="${mediaId}"]`);
  if (!container) return 0;

  const songItems = container.querySelectorAll(".fc-song-item");
  let firstMatch = null;
  let matchCount = 0;
  songItems.forEach(el => {
    const title = (el.querySelector(".s-title")?.textContent || "").toLowerCase();
    const meta = (el.querySelector(".s-meta")?.textContent || "").toLowerCase();
    if (!q || title.includes(q) || meta.includes(q)) {
      el.style.display = "";
      if (!firstMatch && q) firstMatch = el;
      matchCount++;
    } else {
      el.style.display = "none";
    }
  });

  if (firstMatch) {
    firstMatch.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  const moreEl = container.querySelector(".fc-more");
  if (moreEl) moreEl.style.display = (!q && data.hasMore) ? "" : "none";

  return matchCount;
}
