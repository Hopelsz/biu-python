// ---- DOM 辅助 ----
const $ = (id) => document.getElementById(id);
const $$ = (sel, ctx) => (ctx || document).querySelector(sel);
const $$$ = (sel, ctx) => (ctx || document).querySelectorAll(sel);

// 高频 DOM 缓存（热路径如 timeupdate/键盘事件中频繁使用）
const _playerEl = $$(".player");
const _progress = $("progress");
const _curTime = $("cur-time");
const _durTime = $("dur-time");
const _nowTitle = $("now-title");
const _folderSrc = $("folder-src");
const _volume = $("volume");
const _volTip = $("vol-tip");
const _btnPlay = $("btn-play");
const _btnMode = $("btn-mode");
const _volIcon = $("vol-icon");
const _folderList = $("folder-list");
const _headerSearch = $("header-search");
const _titleBar = $$(".title-bar");

// ---- 窗口拖拽 ----
(function() {
  let dragging = false, offsetX = 0, offsetY = 0;

  _titleBar.addEventListener("mousedown", (e) => {
    if (e.target.closest(".win-btn")) return;
    dragging = true;
    offsetX = e.screenX - window.screenX;
    offsetY = e.screenY - window.screenY;
    _titleBar.style.cursor = "grabbing";
  });

  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const x = e.screenX - offsetX;
    const y = e.screenY - offsetY;
    try { window.pywebview.api.move_window(x, y); } catch(ex) {}
  });

  window.addEventListener("mouseup", () => {
    if (dragging) {
      dragging = false;
      _titleBar.style.cursor = "default";
    }
  });
})();

// ---- 状态 ----
let folders = [];
let songs = [];
let currentFolder = null;
let playbackFolder = null; // 当前播放歌曲的来源收藏夹（不随悬浮变化）
let currentIndex = -1;
let isPlaying = false;
let prevVolume = 50;
let playMode = 0; // 0=列表循环 1=单曲循环 2=随机播放
let hiddenFolders = []; // 隐藏的收藏夹 ID 列表
let consecutiveErrors = 0; // 连续播放失败计数
const MODE_ICONS = ["🔁", "🔂", "🔀"];
const MODE_TITLES = ["列表循环", "单曲循环", "随机播放"];

const audio = $("audio");
audio.volume = 0.05;
updateVolIcon();
updateVolSlider(5);

// ---- Cookie ----
function showCookieDialog() {
  $("cookie-dialog").style.display = "flex";
}
function hideCookieDialog() {
  $("cookie-dialog").style.display = "none";
}
async function saveCookie() {
  const val = $("sessdata-input").value.trim();
  if (!val) {
    toast("请输入 SESSDATA");
    return;
  }
  try {
    const resp = await fetch("/api/login", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({sessdata: val})
    });
    const data = await resp.json();
    if (data.ok) {
      hideCookieDialog();
      toast("登录成功");
      _playerEl.style.display = "";
      await loadUser();
      await loadFolders();
    } else {
      toast("登录失败：" + (data.error || "未知错误"));
    }
  } catch (e) {
    toast("请求失败：" + e.message);
  }
}

// ---- Toast ----
let toastTimer;
function toast(msg) {
  const el = $("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 2000);
}

// ---- 用户信息 ----
async function loadUser() {
  const resp = await fetch("/api/user");
  const data = await resp.json();
  const avatarEl = $("user-avatar");
  const loginBtn = $("login-btn");
  if (data.logged_in) {
    const uname = data.uname || ("UID:" + data.mid);
    loginBtn.style.display = "none";
    if (data.face) {
      avatarEl.src = data.face;
      avatarEl.title = uname;
      avatarEl.style.display = "block";
    }
    $("header-search").placeholder = "搜索歌曲...";
  } else {
    loginBtn.style.display = "";
    avatarEl.style.display = "none";
  }
  return data;
}

function toggleAvatarMenu(e) {
  e.stopPropagation();
  $("avatar-dropdown").classList.toggle("show");
}

async function logout() {
  try {
    await fetch("/api/logout", { method: "POST" });
    toast("已退出登录");
    location.reload();
  } catch(e) {
    toast("退出失败");
  }
}

// ---- 隐藏收藏夹配置 ----
async function loadHiddenFolders() {
  try {
    const resp = await fetch("/api/hidden-folders");
    const data = await resp.json();
    hiddenFolders = data.hidden || [];
  } catch(e) { hiddenFolders = []; }
}

// ---- 收藏夹 ----
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

// ---- 设置页面 ----
function showSettings() {
  const list = $("settings-check-list");
  list.innerHTML = folders.map(f => {
    const checked = !hiddenFolders.includes(f.id);
    return `<label class="settings-item">
      <input type="checkbox" data-fid="${f.id}" ${checked ? "checked" : ""}>
      <span class="s-name">${esc(f.title)}</span>
      <span class="s-count">${f.count}首</span>
    </label>`;
  }).join("");
  $("main-area").style.display = "none";
  $("settings-page").style.display = "flex";
  // 始终切到"显示设置"标签
  const displayTab = $$('.settings-tab[data-tab="display"]');
  if (displayTab) switchSettingsTab("display", displayTab);
  loadSystemSettings();
}

function hideSettings() {
  $("settings-page").style.display = "none";
  $("main-area").style.display = "";
}

function switchSettingsTab(tabName, el) {
  $$$(".settings-tab").forEach(t => t.classList.remove("active"));
  $$$(".settings-section[data-tab-content]").forEach(s => s.style.display = "none");
  el.classList.add("active");
  const panel = $$(`.settings-section[data-tab-content="${tabName}"]`);
  if (panel) panel.style.display = "block";
}

async function saveSettings() {
  const checks = $$$("#settings-check-list input[type=checkbox]");
  const newHidden = [];
  checks.forEach(cb => {
    if (!cb.checked) newHidden.push(parseInt(cb.dataset.fid));
  });
  try {
    await fetch("/api/hidden-folders", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({hidden: newHidden})
    });
    hiddenFolders = newHidden;
    hideSettings();
    loadFolders();
    toast("设置已保存");
  } catch(e) {
    toast("保存失败");
  }
}

// ---- 系统设置 ----
const FONT_FAMILIES = {
  "default": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft YaHei", "PingFang SC", sans-serif',
  "noto-sans": '"Noto Sans SC", "Microsoft YaHei", sans-serif',
  "noto-serif": '"Noto Serif SC", "SimSun", Georgia, serif',
  "wenkai": '"LXGW WenKai Mono", "KaiTi", "楷体", serif',
  "xiaowei": '"ZCOOL XiaoWei", "STKaiti", serif',
  "mono": '"Fira Code", "Consolas", "Courier New", "Microsoft YaHei", monospace',
};

async function loadSystemSettings() {
  try {
    const resp = await fetch("/api/system-settings");
    const data = await resp.json();
    const ff = data.font_family || "default";
    const theme = data.theme || "dark";
    setFontSelect(ff);
    applyFontSettings(ff);
    applyTheme(theme);
    // 备注显示开关
    displayRemark = !!data.display_remark;
    $("sys-display-remark").checked = displayRemark;
    // UP显示开关
    showUp = data.show_up !== false;
    $("sys-show-up").checked = showUp;
    // 时长显示开关
    showDuration = data.show_duration !== false;
    $("sys-show-duration").checked = showDuration;
    // 同步 body CSS class（性能优化：替代全量重新渲染）
    document.body.classList.toggle("hide-up", !showUp);
    document.body.classList.toggle("hide-duration", !showDuration);
  } catch(e) {}
}

function applyTheme(theme) {
  document.body.setAttribute("data-theme", theme);
  const btn = $("theme-toggle-btn");
  if (btn) {
    btn.title = theme === "light" ? "切换深色模式" : "切换浅色模式";
  }
}

function applyFontSettings(ff) {
  const family = FONT_FAMILIES[ff] || FONT_FAMILIES["default"];
  document.body.style.fontFamily = family;
  // 预览
  const preview = $("font-preview");
  if (preview) {
    preview.querySelector(".preview-text").style.fontFamily = family;
    preview.querySelector(".preview-text").style.fontSize = "14px";
  }
}

function getFontSelect() {
  const el = $("sys-font-family");
  return el ? el.getAttribute("data-value") || "default" : "default";
}

function setFontSelect(val) {
  const el = $("sys-font-family");
  if (!el) return;
  el.setAttribute("data-value", val);
  const trigger = el.querySelector(".custom-select-trigger");
  const text = el.querySelector(`.custom-select-opt[data-value="${val}"]`);
  if (trigger && text) trigger.textContent = text.textContent;
  // 高亮当前项
  el.querySelectorAll(".custom-select-opt").forEach(o => o.classList.toggle("active", o.getAttribute("data-value") === val));
}

function initFontSelect() {
  const el = $("sys-font-family");
  if (!el) return;
  const trigger = el.querySelector(".custom-select-trigger");
  // 点触发器：开关
  trigger.addEventListener("click", e => { e.stopPropagation(); el.classList.toggle("open"); });
  // 点选项
  el.querySelectorAll(".custom-select-opt").forEach(opt => {
    opt.addEventListener("click", e => {
      e.stopPropagation();
      const val = opt.getAttribute("data-value");
      setFontSelect(val);
      applyFontSettings(val);
      el.classList.remove("open");
    });
  });
}

initFontSelect();
$("theme-toggle-btn").addEventListener("click", function() {
  const current = document.body.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
  saveThemeOnly(next);
});

async function saveThemeOnly(theme) {
  try {
    const resp = await fetch("/api/system-settings");
    const data = await resp.json();
    const ff = data.font_family || "default";
    await fetch("/api/system-settings", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({font_family: ff, theme: theme})
    });
  } catch(e) {}
}

async function saveSystemSettings() {
  const ff = getFontSelect();
  const theme = document.body.getAttribute("data-theme") || "dark";
  const dr = $("sys-display-remark").checked;
  const su = $("sys-show-up").checked;
  const sd = $("sys-show-duration").checked;
  try {
    await fetch("/api/system-settings", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({font_family: ff, theme: theme, display_remark: dr, show_up: su, show_duration: sd})
    });
    applyFontSettings(ff);
    applyRemarkDisplay(dr);
    applyUpDisplay(su);
    applyDurationDisplay(sd);
    toast("设置已保存");
  } catch(e) {
    toast("保存失败");
  }
}

async function toggleRemarkDisplay() {
  const cb = $("sys-display-remark");
  cb.checked = !cb.checked;
  const dr = cb.checked;
  applyRemarkDisplay(dr);
  // 立即持久化到后端
  try {
    await fetch("/api/system-settings", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({display_remark: dr})
    });
  } catch(e) {}
}

async function toggleShowUp() {
  const cb = $("sys-show-up");
  cb.checked = !cb.checked;
  showUp = cb.checked;
  applyUpDisplay(showUp);
  try {
    await fetch("/api/system-settings", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({show_up: showUp})
    });
  } catch(e) {}
}

function applyUpDisplay(val) {
  showUp = val;
  document.body.classList.toggle("hide-up", !val);
}

async function toggleShowDuration() {
  const cb = $("sys-show-duration");
  cb.checked = !cb.checked;
  showDuration = cb.checked;
  applyDurationDisplay(showDuration);
  try {
    await fetch("/api/system-settings", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({show_duration: showDuration})
    });
  } catch(e) {}
}

function applyDurationDisplay(val) {
  showDuration = val;
  document.body.classList.toggle("hide-duration", !val);
}

function toggleAllCheckboxes(e) {
  const checks = $$$("#settings-check-list input[type=checkbox]");
  const allChecked = Array.from(checks).every(cb => cb.checked);
  checks.forEach(cb => { cb.checked = !allChecked; });
  const btn = e.target;
  btn.textContent = allChecked ? "全选" : "全不选";
}

// ---- 播放模式 ----
function togglePlayMode() {
  playMode = (playMode + 1) % 3;
  _btnMode.textContent = MODE_ICONS[playMode];
  _btnMode.title = MODE_TITLES[playMode];
  _btnMode.classList.toggle("loop-one", playMode === 1);
}

// ---- 折叠面板：点击展开/收起收藏夹内容 ----
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

  let html = '<div class="fc-songs">';

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
  if (container) renderFolderContent(mediaId, container);
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

function toggleSearchClear() {
  const input = $("header-search");
  const btn = $("search-clear");
  if (input.value.trim()) {
    btn.classList.add("visible");
  } else {
    btn.classList.remove("visible");
  }
}
function clearSearch() {
  const input = $("header-search");
  input.value = "";
  input.focus();
  toggleSearchClear();
  filterSongs();
}

async function filterSongs() {
  const q = $("header-search").value.trim().toLowerCase();
  const expanded = $$(".folder-item.expanded");

  // 没有展开的收藏夹 → 搜索不生效
  if (!expanded) {
    $("folder-list").classList.remove("no-results");
    return;
  }

  const mediaId = expanded.dataset.id;

  // 清空搜索 → 恢复当前收藏夹完整列表
  if (!q) {
    filterSongsInFolder(mediaId, "");
    $("folder-list").classList.remove("no-results");
    return;
  }

  // 在当前收藏夹内搜索
  const matchCount = filterSongsInFolder(mediaId, q);
  if (matchCount > 0) {
    $("folder-list").classList.remove("no-results");
  } else {
    $("folder-list").classList.add("no-results");
  }
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

  // 自动滚动到第一个匹配项
  if (firstMatch) {
    firstMatch.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // 隐藏/显示"加载更多"按钮
  const moreEl = container.querySelector(".fc-more");
  if (moreEl) moreEl.style.display = (!q && data.hasMore) ? "" : "none";

  return matchCount;
}

function playFolderSong(idx, mediaId) {
  const data = folderContents[mediaId];
  if (!data) return;

  const song = data.items[idx];
  if (!song || !song.bvid) return;

  // 设为当前播放列表
  songs = data.items;
  currentIndex = idx;
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

  playBvidSong(song.bvid, song.title);
}

// 清除所有 .playing 并高亮当前歌曲（统一入口，next/prev/点击共用）
function updatePlayingHighlight(idx) {
  if (!playbackFolder || !playbackFolder.id) return;
  const mediaId = playbackFolder.id;

  // 清除所有播放高亮
  $$$(".fc-song-item.playing").forEach(el => el.classList.remove("playing"));

  // 高亮当前曲目
  const songEl = $$(`.folder-content[data-mid="${mediaId}"] .fc-song-item[data-idx="${idx}"]`);
  if (songEl) {
    songEl.classList.add("playing");
    songEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

// ---- 播放 ----
function playBvidSong(bvid, title) {
  _nowTitle.textContent = "⏳ " + title;
  _nowTitle.title = title;
  // 记录当前歌曲的来源收藏夹（此后不受悬浮影响）
  playbackFolder = currentFolder ? { id: currentFolder.id, title: currentFolder.title } : null;
  // 显示来源收藏夹
  if (playbackFolder && playbackFolder.title) {
    _folderSrc.textContent = "📁 " + playbackFolder.title;
    _folderSrc.style.display = "inline";
  } else {
    _folderSrc.style.display = "none";
  }
  audio.src = `/api/audio?bvid=${bvid}`;
  audio.play().then(() => {
    isPlaying = true;
    updatePlayUI();
  }).catch(() => {
    toast("播放失败");
  });
}

// ---- 定位当前播放歌曲所在收藏夹 ----
function locateCurrentFolder() {
  // 优先使用播放来源，兜底用当前选中
  const folder = playbackFolder || currentFolder;
  if (!folder || !folder.id) return;

  const folderEl = $$(`.folder-item[data-id="${folder.id}"]`);
  if (!folderEl) {
    toast("收藏夹不在当前列表中");
    return;
  }

  // 滚动到目标收藏夹
  folderEl.scrollIntoView({ behavior: "smooth", block: "center" });

  // 高亮 + 闪烁
  $$$(".folder-item").forEach(el => el.classList.remove("active"));
  folderEl.classList.add("active");
  folderEl.classList.add("locate-flash");
  setTimeout(() => folderEl.classList.remove("locate-flash"), 1500);

  // 如果该收藏夹已展开且内容已加载 → 直接定位到当前歌曲
  const contentEl = folderEl.parentElement.querySelector(".folder-content");
  const mediaId = String(folder.id);

  if (contentEl && contentEl.dataset.loaded === "1" && folderContents[mediaId]) {
    // 已加载，确保展开状态
    if (!contentEl.classList.contains("expanded")) {
      collapseAll();
      contentEl.classList.add("expanded");
      folderEl.classList.add("expanded");
      folderEl.querySelector(".arrow").textContent = "▼";
    }
    // 滚动到当前歌曲并高亮
    setTimeout(() => {
      const songEl = contentEl.querySelector(`.fc-song-item[data-idx="${currentIndex}"]`);
      if (songEl) {
        songEl.scrollIntoView({ behavior: "smooth", block: "center" });
        songEl.style.background = `rgba(${themeVar('--accent-rgb')},0.2)`;
        setTimeout(() => { songEl.style.background = ""; }, 2000);
      }
    }, 200);
  } else {
    // 未加载，触发点击展开
    const idx = parseInt(folderEl.dataset.idx);
    toggleFolder(idx);
    // 加载完成后定位歌曲
    setTimeout(() => {
      const songEl = contentEl?.querySelector(`.fc-song-item[data-idx="${currentIndex}"]`);
      if (songEl) {
        songEl.scrollIntoView({ behavior: "smooth", block: "center" });
        songEl.style.background = `rgba(${themeVar('--accent-rgb')},0.2)`;
        setTimeout(() => { songEl.style.background = ""; }, 2000);
      }
    }, 1000);
  }
}

function togglePlay() {
  if (!audio.src) return;
  if (audio.paused) { audio.play(); isPlaying = true; }
  else { audio.pause(); isPlaying = false; }
  updatePlayUI();
}

function nextSong() {
  if (songs.length === 0) return;
  const videos = songs.filter(s => s.type === 2);
  if (videos.length === 0) return;

  let nextIdx;
  if (playMode === 1) {
    // 单曲循环：重复当前
    nextIdx = currentIndex;
  } else if (playMode === 2) {
    // 随机播放
    const videoIndices = videos.map((_, i) => songs.indexOf(videos[i]));
    nextIdx = videoIndices[Math.floor(Math.random() * videoIndices.length)];
  } else {
    // 列表循环：下一首，到末尾回到第一首
    const curVideoIdx = videos.findIndex(v => songs.indexOf(v) === currentIndex);
    if (curVideoIdx >= 0 && curVideoIdx < videos.length - 1) {
      nextIdx = songs.indexOf(videos[curVideoIdx + 1]);
    } else {
      nextIdx = songs.indexOf(videos[0]);
    }
  }

  if (nextIdx >= 0) {
    currentIndex = nextIdx;
    updatePlayingHighlight(nextIdx);
    const song = songs[nextIdx];
    if (song && song.bvid) {
      playBvidSong(song.bvid, song.title);
    }
  }
}

function prevSong() {
  if (songs.length === 0) return;
  const videos = songs.filter(s => s.type === 2);
  if (videos.length === 0) return;

  let prevIdx;
  if (playMode === 2) {
    // 随机
    const videoIndices = videos.map((_, i) => songs.indexOf(videos[i]));
    prevIdx = videoIndices[Math.floor(Math.random() * videoIndices.length)];
  } else {
    // 上一首，到开头回到最后一首
    const curVideoIdx = videos.findIndex(v => songs.indexOf(v) === currentIndex);
    if (curVideoIdx > 0) {
      prevIdx = songs.indexOf(videos[curVideoIdx - 1]);
    } else {
      prevIdx = songs.indexOf(videos[videos.length - 1]);
    }
  }

  if (prevIdx >= 0) {
    currentIndex = prevIdx;
    updatePlayingHighlight(prevIdx);
    const song = songs[prevIdx];
    if (song && song.bvid) {
      playBvidSong(song.bvid, song.title);
    }
  }
}

function seek(val) {
  if (!audio.duration) return;
  audio.currentTime = (val / 100) * audio.duration;
  const acc = themeVar('--accent'), trk = themeVar('--bg-progress-track');
  _progress.style.background = `linear-gradient(to right, ${acc} 0%, ${acc} ${val}%, ${trk} ${val}%, ${trk} 100%)`;
}

function setVolume(val) {
  audio.volume = val / 100;
  updateVolSlider(val);
  updateVolIcon();
  showVolTip(val);
}

function toggleMute() {
  if (audio.volume > 0) { prevVolume = audio.volume * 100; audio.volume = 0; }
  else { audio.volume = prevVolume / 100; }
  const val = audio.volume * 100;
  _volume.value = val;
  updateVolSlider(val);
  updateVolIcon();
}

function updateVolSlider(val) {
  const pct = val || audio.volume * 100;
  const acc = themeVar('--accent'), trk = themeVar('--bg-progress-track');
  _volume.style.background = `linear-gradient(to right, ${acc} 0%, ${acc} ${pct}%, ${trk} ${pct}%, ${trk} 100%)`;
}

function showVolTip(val) {
  _volTip.textContent = Math.round(val);
  const iconW = 26;
  const sliderW = 48;
  _volTip.style.left = (iconW + sliderW * (val / 100)) + "px";
  _volTip.classList.add("show");
  clearTimeout(_volTip._t);
  _volTip._t = setTimeout(() => _volTip.classList.remove("show"), 800);
}

function hideVolTip() {
  clearTimeout(_volTip._t);
  _volTip.classList.remove("show");
}

function updateVolIcon() {
  if (audio.volume === 0) _volIcon.textContent = "🔇";
  else if (audio.volume < 0.5) _volIcon.textContent = "🔉";
  else _volIcon.textContent = "🔊";
}

function updatePlayUI() {
  _btnPlay.textContent = isPlaying ? "⏸" : "▶";
}

// ---- 音频事件 ----
audio.addEventListener("timeupdate", () => {
  if (!audio.duration) return;
  const pct = (audio.currentTime / audio.duration) * 100;
  _progress.value = pct;
  const acc = themeVar('--accent'), trk = themeVar('--bg-progress-track');
  _progress.style.background = `linear-gradient(to right, ${acc} 0%, ${acc} ${pct}%, ${trk} ${pct}%, ${trk} 100%)`;
  _curTime.textContent = formatTime(audio.currentTime);
});

audio.addEventListener("loadedmetadata", () => {
  _durTime.textContent = formatTime(audio.duration);
  _progress.style.background = themeVar('--bg-progress-track');
});

audio.addEventListener("play", () => { isPlaying = true; consecutiveErrors = 0; updatePlayUI(); });
audio.addEventListener("pause", () => { isPlaying = false; updatePlayUI(); });
audio.addEventListener("ended", () => { isPlaying = false; updatePlayUI(); nextSong(); });

audio.addEventListener("error", () => {
  isPlaying = false;
  updatePlayUI();
  consecutiveErrors++;
  if (consecutiveErrors <= 5) {
    toast(`播放失败，已自动跳过 (${consecutiveErrors}/5)`);
    setTimeout(() => nextSong(), 500);
  } else {
    toast("连续播放失败，已停止跳过");
    consecutiveErrors = 0;
  }
});

// ---- 托盘状态查询（供 Python 端 evaluate_js 调用）----
function getPlaybackState() {
  let title = _nowTitle ? _nowTitle.textContent : "未在播放";
  title = title.replace("♫ ", "").replace("⏳ ", "").trim() || "未在播放";
  // 去掉常见的 B 站标题修饰前缀，如 【4K】、【MV】
  title = title.replace(/【[^】]*】/g, "").replace(/\s+/g, " ").trim() || "未在播放";
  return JSON.stringify({ title: title, isPlaying: isPlaying });
}

// ---- 工具 ----
function themeVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
function formatTime(sec) {
  if (!sec || isNaN(sec)) return "--:--";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return m + ":" + String(s).padStart(2, "0");
}
function esc(str) {
  if (!str) return "";
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ---- 全局点击关闭（统一处理下拉菜单、右键菜单、字体选择器）----
document.addEventListener("click", (e) => {
  const target = e.target;
  // 关闭头像下拉
  const dd = $("avatar-dropdown");
  if (dd && !target.closest("#avatar-dropdown") && !target.closest("#user-avatar")) {
    dd.classList.remove("show");
  }
  // 关闭右键菜单
  if (!target.closest("#remark-menu")) hideRemarkMenu();
  // 关闭字体选择器
  const fs = $("sys-font-family");
  if (fs && !target.closest("#sys-font-family")) fs.classList.remove("open");
});

// ---- 键盘快捷键 ----
document.addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT") return;
  switch(e.code) {
    case "Space": e.preventDefault(); togglePlay(); break;
    case "ArrowRight": nextSong(); break;
    case "ArrowLeft": prevSong(); break;
    case "ArrowUp": e.preventDefault(); setVolume(Math.min(100, audio.volume * 100 + 5)); break;
    case "ArrowDown": e.preventDefault(); setVolume(Math.max(0, audio.volume * 100 - 5)); break;
  }
});

// ---- 初始化 ----
(async function init() {
  await loadSystemSettings();
  await loadRemarks();
  const data = await loadUser();
  if (data.logged_in) {
    await loadHiddenFolders();
    await loadFolders();
  } else {
    $("folder-list").innerHTML = `
      <div class="welcome">
        <div class="welcome-icon">🎵</div>
        <div class="welcome-title">BIU</div>
        <div class="welcome-subtitle">轻量级 Bilibili 音乐播放器</div>
        <div class="welcome-features">
          <div class="welcome-feature"><span class="wf-icon">📂</span>同步你的 B 站收藏夹</div>
          <div class="welcome-feature"><span class="wf-icon">🎧</span>在线播放高品质音频</div>
          <div class="welcome-feature"><span class="wf-icon">🔍</span>收藏夹内快速搜索歌曲</div>
        </div>
        <button class="welcome-btn" onclick="showCookieDialog()">登录 Bilibili</button>
        <div class="welcome-footer">登录后即可同步你的收藏夹歌单</div>
      </div>`;
    _playerEl.style.display = "none";
  }
})();
