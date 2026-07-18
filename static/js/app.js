/* BIU - Core: DOM helpers, state, player, utilities */
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
const _lyricsOverlay = $("lyrics-overlay");
const _lyricsBg = $("lyrics-bg");
const _lyricsScroll = $("lyrics-scroll");
const _lyricsScrollInner = $("lyrics-scroll-inner");
const _lyricsSongTitle = $("lyrics-song-title");
const _lyricsSongArtist = $("lyrics-song-artist");
const _lyricsCover = $("lyrics-cover");
const _lyricsCoverPlaceholder = $("lyrics-cover-placeholder");
const _lyricsOffsetBtn = $("lyrics-offset-btn");
const _lyricsOffsetPanel = $("lyrics-offset-panel");
const _lyricsOffsetVal = $("lyrics-offset-val");
const _lyricsControlBar = $("lyrics-control-bar");
const _lyricsCbProgress = $("lyrics-cb-progress");
const _lyricsCbPlaySvg = document.querySelector("#lyrics-cb-play .lyrics-cb-icon-play");
const _lyricsCbPauseSvg = document.querySelector("#lyrics-cb-play .lyrics-cb-icon-pause");
const _lyricsCbCur = $("lyrics-cb-cur");
const _lyricsCbDur = $("lyrics-cb-dur");
const _lyricsCbTranslate = $("lyrics-cb-translate");
const _lyricsSearchBtn = $("lyrics-search-btn");
const _lyricsSearchPanel = $("lyrics-search-panel");
const _lyricsSearchInput = $("lyrics-search-input");
const _lyricsSearchResults = $("lyrics-search-results");

// ---- 窗口拖拽 ----
(function() {
  let dragging = false, offsetX = 0, offsetY = 0, dragEl = null;

  function onDragStart(e) {
    if (e.target.closest(".win-btn")) return;
    dragging = true;
    offsetX = e.screenX - window.screenX;
    offsetY = e.screenY - window.screenY;
    dragEl = e.currentTarget;
    dragEl.style.cursor = "grabbing";
  }

  _titleBar.addEventListener("mousedown", onDragStart);
  const _lyricsDragBar = $("lyrics-drag-bar");
  if (_lyricsDragBar) _lyricsDragBar.addEventListener("mousedown", onDragStart);

  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const x = e.screenX - offsetX;
    const y = e.screenY - offsetY;
    try { window.pywebview.api.move_window(x, y); } catch(ex) {}
  });

  window.addEventListener("mouseup", () => {
    if (dragging) {
      dragging = false;
      if (dragEl) { dragEl.style.cursor = "grab"; dragEl = null; }
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
let retryCount = 0; // 当前歌曲重试计数（失败时先重试同首歌一次）
// 歌词数据模型：{time, endTime, text, translation?, romaji?}
// time/endTime 单位：秒
let lyricsData = [];
let lyricsOpen = false;
let currentLyricIndex = -1;
let lyricsOffset = 0; // 歌词时间偏移量（秒），正数=歌词延后，负数=歌词提前
let lyricsTranslateMode = 0; // 0=仅原文 1=原文+翻译 2=仅翻译
let lyricsIsUserScrolling = false; // 用户是否正在手动滚动歌词
let lyricsScrollTimer = null; // 手动滚动恢复定时器
let lyricsControlTimer = null; // 控制栏自动隐藏定时器
let currentCover = ""; // 当前播放歌曲的封面 URL
let currentArtist = ""; // 当前播放歌曲的 UP 主 / 歌手名
let currentBvid = ""; // 当前播放歌曲的 BV 号（用于歌词搜索）
let currentDuration = 0; // 当前播放歌曲的时长（用于歌词时长匹配）
const MODE_ICONS = ["🔁", "🔂", "🔀"];
const MODE_TITLES = ["列表循环", "单曲循环", "随机播放"];

const audio = $("audio");
audio.volume = 0.05;
updateVolIcon();
updateVolSlider(5);

// ---- Cookie ----
function showCookieDialog() {
  $("cookie-dialog").style.display = "flex";
  // 默认显示扫码登录
  switchLoginTab("qrcode");
  // 自动开始获取二维码
  startQrcodeLogin();
}
function hideCookieDialog() {
  $("cookie-dialog").style.display = "none";
  stopQrcodePolling();
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

// ---- 扫码登录 ----
let qrcodeKey = "";
let qrcodePollTimer = null;

function switchLoginTab(tab) {
  $$(".login-tab.active").classList.remove("active");
  $$(`.login-tab[data-tab="${tab}"]`).classList.add("active");

  if (tab === "qrcode") {
    $("login-qrcode-panel").style.display = "";
    $("login-cookie-panel").style.display = "none";
    if (!qrcodeKey) startQrcodeLogin();
  } else {
    $("login-qrcode-panel").style.display = "none";
    $("login-cookie-panel").style.display = "";
    stopQrcodePolling();
  }
}

async function startQrcodeLogin() {
  stopQrcodePolling();
  $("qrcode-tip").textContent = "正在生成二维码...";
  $("qrcode-refresh-btn").style.display = "none";
  // 显示骨架加载动画
  $("qrcode-skeleton").style.display = "flex";
  $("qrcode-img").style.display = "none";

  try {
    const resp = await fetch("/api/qrcode/generate", { method: "POST" });
    const data = await resp.json();
    if (data.ok) {
      qrcodeKey = data.qrcode_key;
      $("qrcode-img").onload = function() {
        $("qrcode-skeleton").style.display = "none";
        $("qrcode-img").style.display = "";
      };
      $("qrcode-img").src = data.qrcode_image;
      $("qrcode-tip").textContent = "请使用 Bilibili 客户端扫描二维码";
      $("qrcode-refresh-btn").style.display = "";
      // 开始轮询
      startQrcodePolling();
    } else {
      $("qrcode-skeleton").style.display = "none";
      $("qrcode-img").style.display = "";
      $("qrcode-tip").textContent = data.error || "获取二维码失败";
    }
  } catch (e) {
    $("qrcode-skeleton").style.display = "none";
    $("qrcode-img").style.display = "";
    $("qrcode-tip").textContent = "网络错误，请重试";
  }
}

function startQrcodePolling() {
  stopQrcodePolling();
  qrcodePollTimer = setInterval(async () => {
    if (!qrcodeKey) return;
    try {
      const resp = await fetch("/api/qrcode/poll", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ qrcode_key: qrcodeKey })
      });
      const data = await resp.json();

      if (data.status === "success") {
        // 登录成功
        stopQrcodePolling();
        hideCookieDialog();
        toast("扫码登录成功");
        _playerEl.style.display = "";
        await loadUser();
        await loadFolders();
      } else if (data.status === "scanned") {
        $("qrcode-tip").textContent = "已扫码，请在手机上确认登录";
      } else if (data.status === "expired") {
        stopQrcodePolling();
        qrcodeKey = "";
        $("qrcode-mask").style.display = "flex";
        $("qrcode-mask-text").textContent = "二维码已过期";
        $("qrcode-tip").textContent = "二维码已过期，请刷新";
      } else if (data.status === "error") {
        $("qrcode-tip").textContent = data.message || "出错了，请重试";
      }
    } catch (e) {
      // 忽略网络错误，继续轮询
    }
  }, 2000);
}

function stopQrcodePolling() {
  if (qrcodePollTimer) {
    clearInterval(qrcodePollTimer);
    qrcodePollTimer = null;
  }
}

async function refreshQrcode() {
  await startQrcodeLogin();
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


// ---- 播放 ----
function playBvidSong(bvid, title, cover, artist, duration) {
  _nowTitle.textContent = "⏳ " + title;
  _nowTitle.title = title;
  currentCover = cover || "";
  currentArtist = artist || "";
  currentBvid = bvid || "";
  currentDuration = duration || 0;
  // 记录当前歌曲的来源收藏夹（此后不受悬浮影响）
  playbackFolder = currentFolder ? { id: currentFolder.id, title: currentFolder.title } : null;
  // 显示来源收藏夹
  if (playbackFolder && playbackFolder.title) {
    _folderSrc.textContent = "📁 " + playbackFolder.title;
    _folderSrc.style.display = "inline";
  } else {
    _folderSrc.style.display = "none";
  }
  // 如果歌词页已打开，重新拉取歌词
  if (lyricsOpen) {
    lyricsOffset = 0; // 切歌时重置时间偏移
    lyricsTranslateMode = 0; // 重置翻译模式
    lyricsIsUserScrolling = false;
    if (_lyricsOffsetPanel) _lyricsOffsetPanel.style.display = "none";
    _lyricsSongTitle.textContent = title;
    _lyricsSongTitle.title = title;
    _lyricsSongArtist.textContent = currentArtist || "";
    if (currentCover) {
      _lyricsBg.style.backgroundImage = `url(${currentCover}@640w_360h)`;
      _lyricsBg.style.background = "";
      _lyricsCover.src = currentCover + "@320w_320h";
      _lyricsCover.classList.add("show");
    } else {
      _lyricsBg.style.backgroundImage = "";
      _lyricsBg.style.background = "linear-gradient(150deg, #1a1a3e 0%, #16204a 30%, #1a2340 60%, #0f2a3e 100%)";
      _lyricsCover.src = "";
      _lyricsCover.classList.remove("show");
    }
    fetchLyrics(title, currentArtist, bvid, duration);
  } else {
    lyricsData = [];
    currentLyricIndex = -1;
  }
  audio.src = `/api/audio?bvid=${bvid}`;
  audio.play().then(() => {
    isPlaying = true;
    updatePlayUI();
  }).catch(() => {
    toast("播放失败");
  });
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
      playBvidSong(song.bvid, song.title, song.cover || "", song.upper_name || "", song.duration || 0);
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
      playBvidSong(song.bvid, song.title, song.cover || "", song.upper_name || "", song.duration || 0);
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
  // 同步歌词控制栏播放按钮
  if (_lyricsCbPlaySvg && _lyricsCbPauseSvg) {
    _lyricsCbPlaySvg.style.display = isPlaying ? "none" : "";
    _lyricsCbPauseSvg.style.display = isPlaying ? "" : "none";
  }
}

// ---- 音频事件 ----
audio.addEventListener("timeupdate", () => {
  if (!audio.duration) return;
  const pct = (audio.currentTime / audio.duration) * 100;
  _progress.value = pct;
  const acc = themeVar('--accent'), trk = themeVar('--bg-progress-track');
  _progress.style.background = `linear-gradient(to right, ${acc} 0%, ${acc} ${pct}%, ${trk} ${pct}%, ${trk} 100%)`;
  _curTime.textContent = formatTime(audio.currentTime);
  syncLyrics(audio.currentTime);
  // 同步歌词控制栏进度
  if (_lyricsCbProgress) {
    _lyricsCbProgress.value = pct;
    _lyricsCbProgress.style.background = `linear-gradient(to right, #fff 0%, #fff ${pct}%, rgba(255,255,255,.15) ${pct}%, rgba(255,255,255,.15) 100%)`;
  }
  if (_lyricsCbCur) _lyricsCbCur.textContent = formatTime(audio.currentTime);
});

audio.addEventListener("loadedmetadata", () => {
  _durTime.textContent = formatTime(audio.duration);
  if (_lyricsCbDur) _lyricsCbDur.textContent = formatTime(audio.duration);
  _progress.style.background = themeVar('--bg-progress-track');
});

audio.addEventListener("play", () => { isPlaying = true; consecutiveErrors = 0; retryCount = 0; updatePlayUI(); });
audio.addEventListener("pause", () => { isPlaying = false; updatePlayUI(); });
audio.addEventListener("ended", () => { isPlaying = false; updatePlayUI(); nextSong(); });

audio.addEventListener("error", () => {
  isPlaying = false;
  updatePlayUI();

  if (retryCount < 1) {
    // 首次失败：重试同一首歌
    retryCount++;
    toast("播放失败，正在重试...");
    audio.load();
    setTimeout(() => audio.play().catch(() => {}), 300);
  } else {
    // 重试后仍失败：跳过到下一首
    retryCount = 0;
    consecutiveErrors++;
    if (consecutiveErrors <= 5) {
      toast(`播放失败，已自动跳过 (${consecutiveErrors}/5)`);
      setTimeout(() => nextSong(), 500);
    } else {
      toast("连续播放失败，已停止跳过");
      consecutiveErrors = 0;
    }
  }
});


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

// ---- 全局点击关闭（统一处理下拉菜单、右键菜单、字体选择器、搜索面板）----
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
  // 关闭搜索面板
  const sp = $("search-panel");
  if (sp && !target.closest("#search-panel") && !target.closest("#search-wrap")) {
    hideSearchPanel();
  }
});

document.addEventListener("keydown", e => {
  // Ctrl+F / Ctrl+K → 聚焦搜索框
  if ((e.ctrlKey || e.metaKey) && (e.code === "KeyF" || e.code === "KeyK")) {
    e.preventDefault();
    const input = $("header-search");
    input.focus();
    input.select();
    return;
  }
  if (e.target.tagName === "INPUT") return;
  switch(e.code) {
    case "Space": e.preventDefault(); togglePlay(); break;
    case "ArrowRight": nextSong(); break;
    case "ArrowLeft": prevSong(); break;
    case "ArrowUp": e.preventDefault(); setVolume(Math.min(100, audio.volume * 100 + 5)); break;
    case "ArrowDown": e.preventDefault(); setVolume(Math.max(0, audio.volume * 100 - 5)); break;
  }
});
