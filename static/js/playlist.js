/* BIU - Folder & Playlist Functions */
async function loadFolders() {
  const list = $("folder-list");
  list.innerHTML = '<div class="loading"><div class="spinner"></div>加载中...</div>';
  const resp = await fetch("/api/folders");
  folders = await resp.json();
  if (!folders.length) {
    list.innerHTML = '<div class="empty">暂无收藏夹</div>';
    return;
  }
  const visible = folders.filter(f => !hiddenFolders.includes(f.id));
  if (!visible.length) {
    list.innerHTML = '<div class="empty">所有收藏夹已隐藏<br><a href="#" onclick="showSettings()" class="link-accent" style="font-size:11px;">去设置中显示</a></div>';
    return;
  }
  let html = visible.map((f, i) => {
    const realIdx = folders.indexOf(f);
    return `
    <div class="folder-wrap">
      <div class="folder-item"
           data-idx="${realIdx}"
           data-id="${f.id}"
           onclick="toggleFolder(${realIdx})">
        <span class="folder-cover-placeholder" data-mid="${f.id}">📁</span>
        <span class="folder-name">${esc(f.title)}</span>
        <span class="folder-count">${f.count}首</span>
        <button class="folder-refresh" title="刷新" onclick="refreshFolder(event, ${f.id}, ${realIdx})">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
        </button>
        <span class="arrow">▶</span>
      </div>
      <div class="folder-content" data-mid="${f.id}" data-loaded="0"></div>
    </div>
  `;}).join("");
  const hiddenCnt = hiddenFolders.filter(id => folders.some(f => f.id === id)).length;
  if (hiddenCnt > 0) {
    html += `<div class="hidden-hint" onclick="showSettings()">已隐藏 ${hiddenCnt} 个收藏夹 · 点击管理</div>`;
  }
  list.innerHTML = html;
  // 异步加载封面图
  loadFolderCovers(visible);
}

async function loadFolderCovers(folderList) {
  for (const f of folderList) {
    try {
      const resp = await fetch(`/api/folder-info?media_id=${f.id}`);
      const info = await resp.json();
      if (info && info.cover) {
        const placeholder = $$(`.folder-cover-placeholder[data-mid="${f.id}"]`);
        if (placeholder) {
          placeholder.outerHTML = `<img class="folder-cover" src="${esc(info.cover)}" onerror="this.replaceWith(document.createTextNode('📁'))" />`;
        }
      }
    } catch(e) { /* 封面加载失败，保留占位符 */ }
  }
}


let folderContents = {}; // { media_id: { items:[], hasMore:bool, page:int, title:str } }

function collapseAll() {
  $$$(".folder-content.expanded").forEach(el => {
    el.classList.remove("expanded");
  });
  $$$(".folder-item.expanded").forEach(el => el.classList.remove("expanded"));
  $$$(".folder-wrap.expanded").forEach(el => el.classList.remove("expanded"));
  $$$(".folder-item .arrow").forEach(el => el.textContent = "▶");
}

function toggleFolder(idx) {
  const folder = folders[idx];
  if (!folder) return;

  const itemEl = $$(`.folder-item[data-idx="${idx}"]`);
  if (!itemEl) return;
  const contentEl = itemEl.parentElement.querySelector(".folder-content");
  if (!contentEl) return;
  const arrowEl = itemEl.querySelector(".arrow");

  // 如果已展开 → 收起
  if (contentEl.classList.contains("expanded")) {
    contentEl.classList.remove("expanded");
    itemEl.classList.remove("expanded");
    itemEl.parentElement.classList.remove("expanded");
    arrowEl.textContent = "▶";
    return;
  }

  // 收起其他展开项（手风琴模式）
  collapseAll();

  // 展开当前项
  contentEl.classList.add("expanded");
  itemEl.classList.add("expanded");
  itemEl.parentElement.classList.add("expanded");
  arrowEl.textContent = "▼";

  // 高亮当前项
  $$$(".folder-item").forEach(el => el.classList.remove("active"));
  itemEl.classList.add("active");
  currentFolder = folder;

  // 滚动使展开项可见（替代 order:-1，避免 sticky 在 flex 中异常）
  itemEl.scrollIntoView({ behavior: "smooth", block: "start" });

  // 加载内容（只加载一次）
  if (contentEl.dataset.loaded === "0") {
    loadFolderContent(folder.id, contentEl);
  }
}

async function loadFolderContent(mediaId, container) {
  container.innerHTML = '<div class="loading" style="padding:12px;font-size:12px;height:auto"><div class="spinner"></div>加载中...</div>';
  try {
    const resp = await fetch(`/api/folder-content?media_id=${mediaId}&page=1`);
    const data = await resp.json();
    const items = data.items || [];

    if (!items.length) {
      container.innerHTML = '<div class="fc-empty">' + (data.error || '暂无内容') + '</div>';
      container.dataset.loaded = "1";
      return;
    }

    // 记住所属收藏夹标题
    const folder = folders.find(f => f.id === mediaId);
    folderContents[mediaId] = {
      items: items,
      hasMore: data.has_more || false,
      page: 1,
      title: folder ? folder.title : ""
    };
    container.dataset.loaded = "1";
    renderFolderContent(mediaId, container);

    // 用内容 API 返回的真实 total 修正收藏夹显示的数字
    updateFolderCountDisplay(mediaId, data.total);
  } catch(e) {
    container.innerHTML = '<div class="fc-empty">加载失败</div>';
    container.dataset.loaded = "1";
  }
}

async function refreshFolder(e, mediaId, idx) {
  e.stopPropagation();
  const container = $$(`.folder-content[data-mid="${mediaId}"]`);
  if (!container) return;
  // 确保展开
  const itemEl = $$(`.folder-item[data-idx="${idx}"]`);
  const contentEl = itemEl ? itemEl.parentElement.querySelector(".folder-content") : null;
  if (contentEl && !contentEl.classList.contains("expanded")) {
    contentEl.classList.add("expanded");
    contentEl.dataset.loaded = "0";
    if (itemEl) { itemEl.classList.add("expanded"); itemEl.querySelector(".arrow").textContent = "▼"; }
    if (itemEl) itemEl.parentElement.classList.add("expanded");
  }
  // 给按钮加旋转动画
  const btn = e.currentTarget;
  btn.classList.add("spinning");
  try {
    await loadFolderContent(mediaId, container);
  } finally {
    btn.classList.remove("spinning");
  }
}

// ---- 歌曲备注 ----
let remarks = {};
let displayRemark = false;
let showUp = true;
let showDuration = true;
let menuBvid = "";  // 当前右键菜单所在的 bvid
let menuIdx = -1;   // 当前右键菜单歌曲的索引
let menuMediaId = ""; // 当前右键菜单歌曲所属收藏夹 ID
let _savingRemark = false; // 防止重复保存

async function loadRemarks() {
  try {
    const resp = await fetch("/api/remarks");
    remarks = await resp.json();
  } catch(e) { remarks = {}; }
}

function applyRemarkDisplay(val) {
  displayRemark = val;
  const containers = $$$("[data-loaded='1']");
  containers.forEach(c => {
    const mediaId = c.dataset.mid;
    if (mediaId && folderContents[mediaId]) {
      renderFolderContent(mediaId, c);
    }
  });
}

// ---- 右键菜单 ----
function showRemarkMenu(e, bvid, idx, mediaId) {
  e.preventDefault();
  e.stopPropagation();
  menuBvid = bvid;
  menuIdx = idx;
  menuMediaId = mediaId;
  const menu = $("remark-menu");
  const hasRemark = !!remarks[bvid];
  $("rm-delete").style.display = hasRemark ? "" : "none";
  menu.style.display = "block";
  // 定位在鼠标附近，防止出界
  let x = e.clientX, y = e.clientY;
  // 菜单高度：播放(32) + 编辑(32) + 删除(32 if hasRemark else 0) = 64~96px
  const menuH = hasRemark ? 96 : 64;
  if (x + 120 > window.innerWidth) x -= 120;
  if (y + menuH > window.innerHeight) y -= menuH;
  menu.style.left = x + "px";
  menu.style.top = y + "px";
}

function hideRemarkMenu() {
  $("remark-menu").style.display = "none";
  menuBvid = "";
  menuIdx = -1;
  menuMediaId = "";
}

function playFromMenu() {
  const idx = menuIdx;
  const mediaId = menuMediaId;
  hideRemarkMenu();
  if (idx < 0 || !mediaId) return;
  playFolderSong(idx, mediaId);
}

function startEditRemarkFromMenu() {
  const bvid = menuBvid;
  hideRemarkMenu();
  if (!bvid) return;
  startEditRemark(bvid);
}

function deleteRemarkFromMenu() {
  const bvid = menuBvid;
  hideRemarkMenu();
  if (!bvid) return;
  // 没有输入框，直接通过 finishEditRemark 处理（传空值即删除）
  finishEditRemark(bvid, "");
}

function startEditRemark(bvid) {
  const titleEl = $$(`.s-title[data-remark-bvid="${bvid}"]`);
  if (!titleEl) return;
  const cur = remarks[bvid] || "";
  // 记住原始 HTML 用于还原
  titleEl.dataset.origHtml = titleEl.innerHTML;
  titleEl.innerHTML = `<input class="remark-input" value="${esc(cur)}" maxlength="80"
    onkeydown="if(event.key==='Enter'){event.preventDefault();finishEditRemark('${bvid}',this.value);}if(event.key==='Escape')cancelEditRemark('${bvid}')"
    onblur="cancelEditRemark('${bvid}')">`;
  const input = titleEl.querySelector(".remark-input");
  input.focus();
  input.select();
}

// 还原单个输入框为正常显示（不刷新整个列表）
function revertEditInput(bvid) {
  const titleEl = $$(`.s-title[data-remark-bvid="${bvid}"]`);
  if (!titleEl || !titleEl.dataset.origHtml) return;
  titleEl.innerHTML = titleEl.dataset.origHtml;
  delete titleEl.dataset.origHtml;
}

function finishEditRemark(bvid, val) {
  if (_savingRemark) return;
  val = (val || "").trim();

  // 值没变，直接还原输入框
  if (val === (remarks[bvid] || "")) {
    revertEditInput(bvid);
    return;
  }

  _savingRemark = true;
  const prevRemark = remarks[bvid];

  // 乐观更新：立即更新本地状态
  if (val) {
    remarks[bvid] = val;
    if (!displayRemark) {
      displayRemark = true;
      const toggle = $("sys-display-remark");
      if (toggle) toggle.checked = true;
    }
  } else {
    delete remarks[bvid];
  }

  // 立即刷新 UI（容器 innerHTML 被整体替换，输入框自然消失，无需 revertEditInput）
  refreshAllSongs();

  // 后台异步保存到后端
  (async () => {
    try {
      const resp = await fetch("/api/remarks", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({bvid, remark: val})
      });
      const data = await resp.json();
      if (data.ok) {
        // 持久化 display_remark 到后端
        if (displayRemark) {
          fetch("/api/system-settings", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({display_remark: true})
          }).catch(()=>{});
        }
        toast(val ? "备注已保存" : "备注已删除");
      } else {
        // 回滚
        if (prevRemark) remarks[bvid] = prevRemark;
        else delete remarks[bvid];
        refreshAllSongs();
        toast("保存失败");
      }
    } catch(e) {
      // 回滚
      if (prevRemark) remarks[bvid] = prevRemark;
      else delete remarks[bvid];
      refreshAllSongs();
      toast("保存失败，请检查网络");
    }
    _savingRemark = false;
  })();
}

function cancelEditRemark(bvid) {
  revertEditInput(bvid);
}

function refreshAllSongs() {
  const containers = $$$("[data-loaded='1']");
  containers.forEach(c => {
    const mediaId = c.dataset.mid;
    if (mediaId && folderContents[mediaId]) {
      renderFolderContent(mediaId, c);
    }
  });
}

function renderFolderContent(mediaId, container) {
  const data = folderContents[mediaId];
  if (!data) return;

  let html = '<div class="fc-filter-wrap"><input class="fc-filter" type="text" placeholder="过滤歌曲..." oninput="onFolderFilter(this, \'' + mediaId + '\')"><button class="fc-filter-clear" onclick="clearFolderFilter(\'' + mediaId + '\')" title="清空">✕</button></div>';
  html += '<div class="fc-songs">';

  data.items.forEach((s, i) => {
    if (s.type !== 2) return;
    const dur = s.duration ? formatTime(s.duration) : "";
    const isPlaying = i === currentIndex && playbackFolder && playbackFolder.id == mediaId;
    const bvid = s.bvid || "";
    const remark = remarks[bvid] || "";
    const showRemark = displayRemark && remark;

    html += `<div class="fc-song-item${isPlaying ? " playing" : ""}"
                  data-idx="${i}" data-bvid="${esc(bvid)}"
                  ondblclick="playFolderSong(${i}, '${mediaId}')"
                  oncontextmenu="showRemarkMenu(event, '${esc(bvid)}', ${i}, '${mediaId}')"
                  title="${esc(s.title)}">
      <span class="idx">${i + 1}</span>
      <span class="s-title" data-remark-bvid="${esc(bvid)}">
        <span class="s-title-text${showRemark ? ' remark-text' : ''}">${esc(showRemark ? remark : s.title)}</span>
      </span>
      <span class="s-meta">${esc(s.upper_name||'')}</span>
      <span class="s-dur">${dur}</span>
    </div>`;
  });

  html += '</div>';
  if (data.hasMore) {
    html += '<div class="fc-more"><button id="fc-more-btn-' + mediaId + '" onclick="loadMoreFolderContent(\'' + mediaId + '\')">加载更多</button></div>';
  }

  container.innerHTML = html;
}

async function loadMoreFolderContent(mediaId) {
  const data = folderContents[mediaId];
  if (!data) return;
  const nextPage = data.page + 1;

  const btn = $$(`#fc-more-btn-${mediaId}`);
  if (btn) btn.textContent = "加载中...";

  const resp = await fetch(`/api/folder-content?media_id=${mediaId}&page=${nextPage}`);
  const result = await resp.json();
  const newItems = result.items || [];

  data.items = data.items.concat(newItems);
  data.hasMore = result.has_more || false;
  data.page = nextPage;

  // 全部加载完成时，用实际条目数更新显示数字（最准确）
  if (!data.hasMore) {
    updateFolderCountDisplay(mediaId, data.items.length);
  }

  const container = $$(`.folder-content[data-mid="${mediaId}"]`);
  if (container) {
    // 保存并恢复过滤状态
    const filterInput = container.querySelector(".fc-filter");
    const q = filterInput ? filterInput.value : "";
    renderFolderContent(mediaId, container);
    if (q) {
      const newInput = container.querySelector(".fc-filter");
      if (newInput) newInput.value = q;
      onFolderFilter({ value: q }, mediaId);
    }
  }
}

// ---- 收藏夹内过滤 ----
function onFolderFilter(input, mediaId) {
  const q = input.value.trim().toLowerCase();
  const clearBtn = input.parentElement.querySelector(".fc-filter-clear");
  if (clearBtn) clearBtn.classList.toggle("visible", !!q);
  const cnt = filterSongsInFolder(mediaId, q);
  const list = $("folder-list");
  if (list) list.classList.toggle("no-results", q && cnt === 0);
}

function clearFolderFilter(mediaId) {
  const container = $$(`.folder-content[data-mid="${mediaId}"]`);
  if (!container) return;
  const input = container.querySelector(".fc-filter");
  if (input) {
    input.value = "";
    onFolderFilter(input, mediaId);
    input.focus();
  }
}

function playFolderSong(idx, mediaId) {
  const data = folderContents[mediaId];
  if (!data) return;

  const song = data.items[idx];
  if (!song || !song.bvid) return;

  // 设为当前播放列表
  songs = data.items.filter(s => s.type === 2);
  currentIndex = songs.findIndex(s => s.bvid === song.bvid);
  if (currentIndex < 0) currentIndex = idx;
  currentFolder = { id: mediaId, title: data.title };
  playbackFolder = { id: mediaId, title: data.title };

  // 高亮对应收藏夹
  $$$(".folder-item").forEach(el => el.classList.remove("active"));
  const folderItem = $$(`.folder-item[data-id="${mediaId}"]`);
  if (folderItem) folderItem.classList.add("active");

  // 更新底部来源标签
  _folderSrc.textContent = "📁 " + (data.title || "收藏夹");
  _folderSrc.style.display = "inline";

  // 高亮当前播放曲目
  updatePlayingHighlight(idx);

  playBvidSong(song.bvid, song.title, song.cover || "", song.upper_name || "", song.duration || 0);
}

function updateFolderCountDisplay(mediaId, realCount) {
  if (!realCount || realCount <= 0) return;
  // 更新 folders 数组，防止重新渲染时回退
  const folder = folders.find(f => f.id === mediaId);
  if (!folder || folder.count === realCount) return;
  folder.count = realCount;
  // 更新 DOM 中的数字
  const el = $$(`.folder-item[data-id="${mediaId}"] .folder-count`);
  if (el) el.textContent = `${realCount}首`;
}

// ---- 托盘状态查询（供 Python 端 evaluate_js 调用）----
function getPlaybackState() {
  let title = _nowTitle ? _nowTitle.textContent : "未在播放";
  title = title.replace("♫ ", "").replace("⏳ ", "").trim() || "未在播放";
  // 去掉常见的 B 站标题修饰前缀，如 【4K】、【MV】
  title = title.replace(/【[^】]*】/g, "").replace(/\s+/g, " ").trim() || "未在播放";
  return JSON.stringify({ title: title, isPlaying: isPlaying });
}
