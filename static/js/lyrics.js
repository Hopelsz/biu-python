/* BIU - Lyrics Functions */
// ---- 全屏歌词 ----
// 参考 BBPlayer 的 LRC/SPL 解析思路，支持多时间戳、结束时间计算
function _parseTimeTag(timeStr) {
  // 解析 [mm:ss.xx] 或 <mm:ss.xx> 格式，返回秒数
  const clean = timeStr.replace(/[\[\]<>]/g, "");
  const parts = clean.split(":");
  if (parts.length < 2) return -1;
  const mins = parseInt(parts[0]) || 0;
  const secParts = (parts[1] || "0").split(".");
  const secs = parseInt(secParts[0]) || 0;
  let ms = 0;
  if (secParts[1]) {
    // 兼容变长毫秒：.5→500ms, .50→500ms, .500→500ms, .123456→123ms
    const msStr = secParts[1].padEnd(3, "0").slice(0, 3);
    ms = parseInt(msStr) || 0;
  }
  return mins * 60 + secs + ms / 1000;
}

function parseLRC(lrc) {
  if (!lrc) return [];
  
  const lines = lrc.split("\n");
  const rawLines = [];
  const timeRe = /\[(\d{1,3}:\d{2}(?:[.:]\d{1,6})?)\]/g;
  const metaRe = /^\[(ti|ar|al|by|offset|re|ve|la):(.+)\]$/i;
  const endTimeRe = /<(\d{1,3}:\d{2}(?:[.:]\d{1,6})?)>/g;
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    
    // 跳过来自网易云的翻译/罗马音行元数据（在 API 层合并处理）
    const metaMatch = trimmed.match(metaRe);
    if (metaMatch && trimmed.replace(metaRe, "").trim() === "") continue;
    
    // 提取所有时间戳
    const timestamps = [];
    let match;
    timeRe.lastIndex = 0;
    while ((match = timeRe.exec(trimmed)) !== null) {
      timestamps.push(_parseTimeTag(match[0]));
    }
    
    if (timestamps.length === 0) continue;
    
    // 提取文本（去掉所有时间标签和结束时间标签）
    let text = trimmed.replace(timeRe, "").replace(endTimeRe, "").trim();
    
    rawLines.push({
      timestamps: timestamps,
      text: text,
      raw: trimmed,
    });
  }
  
  // 多时间戳行展开：每个时间戳独立成一行
  const expanded = [];
  for (const rl of rawLines) {
    for (const ts of rl.timestamps) {
      if (rl.text) {
        expanded.push({ time: ts, text: rl.text });
      }
    }
  }
  
  // 按时间排序
  expanded.sort((a, b) => a.time - b.time);
  
  // 去重（相邻时间戳 + 相同文本视为重复）
  const deduped = [];
  for (let i = 0; i < expanded.length; i++) {
    if (i > 0 && 
        expanded[i].time === expanded[i-1].time && 
        expanded[i].text === expanded[i-1].text) {
      continue;
    }
    deduped.push(expanded[i]);
  }
  
  // 计算每行的 endTime（下一行时间或默认 +5秒）
  for (let i = 0; i < deduped.length; i++) {
    if (i < deduped.length - 1) {
      deduped[i].endTime = Math.min(deduped[i+1].time, deduped[i].time + 10);
    } else {
      deduped[i].endTime = deduped[i].time + 10;
    }
  }
  
  return deduped;
}

// 解析并合并翻译歌词（如果存在 tlyric/romalrc）
function parseAndMergeLyrics(lrc, tlyric, romalrc) {
  const mainLines = parseLRC(lrc);
  if (mainLines.length === 0) return [];
  
  // 解析翻译和罗马音
  const transLines = tlyric ? parseLRC(tlyric) : [];
  const romajiLines = romalrc ? parseLRC(romalrc) : [];
  
  // 基于时间戳匹配：将翻译/罗马音按时间戳映射
  function buildMap(srcLines) {
    const map = {};
    for (const l of srcLines) {
      if (!map[l.time]) map[l.time] = l.text;
    }
    return map;
  }
  
  const transMap = buildMap(transLines);
  const romajiMap = buildMap(romajiLines);
  
  // 计算匹配度（参考 BBPlayer 的 isMatch 逻辑，至少20%匹配）
  function calcMatchRate(srcLines, mainSet) {
    if (srcLines.length === 0) return 0;
    let match = 0;
    for (const l of srcLines) {
      if (mainSet.has(l.time)) match++;
    }
    return match / srcLines.length;
  }
  
  const mainTimeSet = new Set(mainLines.map(l => l.time));
  const transMatchRate = calcMatchRate(transLines, mainTimeSet);
  const romajiMatchRate = calcMatchRate(romajiLines, mainTimeSet);
  
  // 合并
  const merged = mainLines.map(l => {
    const result = { ...l };
    if (transMatchRate >= 0.2 && transMap[l.time] !== undefined) {
      // 使用最近时间匹配（±0.3秒容差）
      result.translation = transMap[l.time];
    } else if (transMatchRate >= 0.2) {
      // 时间模糊匹配
      for (const t of Object.keys(transMap).map(Number).sort()) {
        if (Math.abs(l.time - t) < 0.35) {
          result.translation = transMap[t];
          break;
        }
      }
    }
    if (romajiMatchRate >= 0.2 && romajiMap[l.time] !== undefined) {
      result.romaji = romajiMap[l.time];
    } else if (romajiMatchRate >= 0.2) {
      for (const t of Object.keys(romajiMap).map(Number).sort()) {
        if (Math.abs(l.time - t) < 0.35) {
          result.romaji = romajiMap[t];
          break;
        }
      }
    }
    return result;
  });
  
  const hasTranslation = merged.some(l => l.translation);
  const hasRomaji = merged.some(l => l.romaji);
  
  return { lines: merged, hasTranslation, hasRomaji };
}

function renderLyrics() {
  if (!_lyricsScrollInner) return;
  if (lyricsData.length === 0) {
    _lyricsScrollInner.innerHTML = '<div class="lyric-page-line lyric-page-empty">暂无歌词</div>';
    if (_lyricsCbTranslate) _lyricsCbTranslate.style.display = "none";
    return;
  }
  
  // 检查是否有翻译/罗马音可用
  const hasTranslation = lyricsData.some(l => l.translation);
  const hasRomaji = lyricsData.some(l => l.romaji);
  
  if (hasTranslation || hasRomaji) {
    if (_lyricsCbTranslate) {
      _lyricsCbTranslate.style.display = "";
      if (lyricsTranslateMode === 0) {
        _lyricsCbTranslate.textContent = hasTranslation ? "译" : "音";
        _lyricsCbTranslate.title = "点击显示翻译";
      } else {
        _lyricsCbTranslate.textContent = "原";
        _lyricsCbTranslate.title = lyricsTranslateMode === 1 ? "点击隐藏翻译" : "点击显示原文";
      }
    }
  } else {
    if (_lyricsCbTranslate) _lyricsCbTranslate.style.display = "none";
  }
  
  _lyricsScrollInner.innerHTML = lyricsData.map((l, i) => {
    let html = "";
    
    // 主文本
    if (lyricsTranslateMode !== 2) {
      html += `<div class="lyric-page-line-text">${esc(l.text)}</div>`;
    }
    
    // 翻译/罗马音
    if (lyricsTranslateMode >= 1) {
      const sub = l.romaji || l.translation || "";
      if (sub) {
        html += `<div class="lyric-page-line-sub">${esc(sub)}</div>`;
      }
    }
    
    // 只在原文模式时也可能显示翻译（如果是仅原文模式，不显示翻译行）
    
    const cls = "lyric-page-line" + (lyricsTranslateMode !== 0 ? " lyric-page-line-dual" : "");
    return `<div class="${cls}" data-lyric-idx="${i}" data-time="${l.time}">${html}</div>`;
  }).join("");
  currentLyricIndex = -1;
}

// 二分查找：找到 adjustedTime 对应的最后的歌词行索引
function _findLyricIndex(time) {
  let lo = 0, hi = lyricsData.length - 1;
  let result = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (lyricsData[mid].time <= time) {
      result = mid;
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  return result;
}

function syncLyrics(currentTime) {
  if (!lyricsOpen || lyricsData.length === 0) return;
  
  const adjustedTime = currentTime + lyricsOffset;
  const idx = _findLyricIndex(adjustedTime);
  
  if (idx === currentLyricIndex) return;
  
  // 移除旧高亮
  _lyricsScrollInner.querySelectorAll(".lyric-page-line.current").forEach(el => el.classList.remove("current"));
  
  if (idx >= 0) {
    const newEl = _lyricsScrollInner.querySelector(`[data-lyric-idx="${idx}"]`);
    if (newEl) {
      newEl.classList.add("current");
      // 当前行居中平滑滚动（仅在非用户滚动时）
      if (!lyricsIsUserScrolling) {
        const containerH = _lyricsScroll.clientHeight;
        const targetY = newEl.offsetTop - containerH / 2 + newEl.offsetHeight / 2 + newEl.offsetHeight;
        _lyricsScroll.scrollTo({
          top: Math.max(0, Math.min(targetY, _lyricsScroll.scrollHeight - containerH)),
          behavior: "smooth"
        });
      }
    }
  }
  currentLyricIndex = idx;
}

// 用户手动滚动歌词 -> 暂停自动跟随
function _onLyricsUserScrollStart() {
  lyricsIsUserScrolling = true;
  clearTimeout(lyricsScrollTimer);
}

function _onLyricsUserScrollEnd() {
  // 2秒后恢复自动滚动（参考 BBPlayer 的方案）
  clearTimeout(lyricsScrollTimer);
  lyricsScrollTimer = setTimeout(() => {
    lyricsIsUserScrolling = false;
    // 自动滚动到当前歌词行
    if (currentLyricIndex >= 0) {
      const el = _lyricsScrollInner.querySelector(`[data-lyric-idx="${currentLyricIndex}"]`);
      if (el) {
        const containerH = _lyricsScroll.clientHeight;
        const targetY = el.offsetTop - containerH / 2 + el.offsetHeight / 2 + el.offsetHeight;
        _lyricsScroll.scrollTo({ top: Math.max(0, Math.min(targetY, _lyricsScroll.scrollHeight - containerH)), behavior: "smooth" });
      }
    }
  }, 2000);
}

// 点击歌词行跳转到对应时间
function _onLyricLineClick(e) {
  const lineEl = e.target.closest(".lyric-page-line");
  if (!lineEl) return;
  const idx = parseInt(lineEl.dataset.lyricIdx);
  const time = parseFloat(lineEl.dataset.time);
  if (isNaN(idx) || isNaN(time)) return;
  
  // 跳转播放进度（考虑偏移量）
  // offset>0 时歌词延后，所以点击的歌词行对应音频时间 = 歌词时间戳 - offset
  const seekTime = time - lyricsOffset;
  audio.currentTime = Math.max(0, seekTime);
  toast("已跳转至 " + formatTime(seekTime));
}

function openLyrics() {
  // 如果没有在播放，不打开
  if (!audio.src || _nowTitle.textContent.indexOf("未在播放") >= 0) return;
  lyricsOpen = true;
  lyricsOffset = 0; // 重置时间偏移
  lyricsTranslateMode = 0; // 重置翻译模式
  lyricsIsUserScrolling = false;
  // 设置封面图（前景）
  if (currentCover) {
    _lyricsCover.src = currentCover + "@320w_320h";
    _lyricsCover.classList.add("show");
  } else {
    _lyricsCover.src = "";
    _lyricsCover.classList.remove("show");
  }
  // 设置模糊背景
  if (currentCover) {
    _lyricsBg.style.backgroundImage = `url(${currentCover}@640w_360h)`;
    _lyricsBg.style.background = "";
  } else {
    _lyricsBg.style.backgroundImage = "";
    _lyricsBg.style.background = "linear-gradient(150deg, #1a1a3e 0%, #16204a 30%, #1a2340 60%, #0f2a3e 100%)";
  }
  // 设置标题
  const _t = _nowTitle.title || _nowTitle.textContent.replace("♫ ", "").replace("⏳ ", "");
  _lyricsSongTitle.textContent = _t;
  _lyricsSongTitle.title = _t;
  _lyricsSongArtist.textContent = currentArtist || "";
  // 显示覆盖层
  _lyricsOverlay.classList.remove("closing");
  _lyricsOverlay.classList.add("show");
  // 初始化控制栏：显示状态同步 + 3秒自动隐藏
  showLyricsControls();
  updatePlayUI();
  // 同步控制栏进度
  if (audio.duration) {
    const pct = (audio.currentTime / audio.duration) * 100;
    if (_lyricsCbProgress) {
      _lyricsCbProgress.value = pct;
      _lyricsCbProgress.style.background = `linear-gradient(to right, #fff 0%, #fff ${pct}%, rgba(255,255,255,.15) ${pct}%, rgba(255,255,255,.15) 100%)`;
    }
    if (_lyricsCbCur) _lyricsCbCur.textContent = formatTime(audio.currentTime);
    if (_lyricsCbDur) _lyricsCbDur.textContent = formatTime(audio.duration);
  }
  // 如果已有歌词数据，重新渲染；否则触发加载
  if (lyricsData.length > 0) {
    renderLyrics();
    // 同步当前播放位置
    syncLyrics(audio.currentTime);
  } else {
    _lyricsScrollInner.innerHTML = '<div class="lyric-page-line lyric-page-loading">歌词加载中...</div>';
    fetchLyrics(_nowTitle.title || "", currentArtist, currentBvid, currentDuration);
  }
  // ESC 关闭
  document.addEventListener("keydown", _onLyricsKey);
}

function closeLyrics() {
  lyricsOpen = false;
  _lyricsOverlay.classList.add("closing");
  document.removeEventListener("keydown", _onLyricsKey);
  if (_lyricsOffsetPanel) _lyricsOffsetPanel.style.display = "none";
  if (_lyricsSearchPanel) _lyricsSearchPanel.style.display = "none";
  if (_lyricsMoreMenu) _lyricsMoreMenu.style.display = "none";
  clearTimeout(lyricsControlTimer);
  if (_lyricsControlBar) _lyricsControlBar.classList.remove("visible");
  // 清理隐藏状态，确保下次打开时按钮可见
  document.querySelectorAll(".lyrics-close, .lyrics-ctrls").forEach(el => el.classList.remove("lyrics-ui-hidden"));
  setTimeout(() => {
    _lyricsOverlay.classList.remove("show", "closing");
  }, 250);
}

function _onLyricsKey(e) {
  if (e.key === "Escape") {
    // 如果搜索面板打开，先关闭搜索面板
    if (_lyricsSearchPanel && _lyricsSearchPanel.style.display === "flex") {
      _lyricsSearchPanel.style.display = "none";
      return;
    }
    // 如果更多菜单打开，先关闭更多菜单
    if (_lyricsMoreMenu && _lyricsMoreMenu.style.display === "flex") {
      _lyricsMoreMenu.style.display = "none";
      return;
    }
    closeLyrics();
  } else if (e.key === "[" || e.key === "]") {
    // 歌词时间偏移调整：每按一次 ±0.5 秒
    e.preventDefault();
    lyricsOffset += (e.key === "]") ? 0.5 : -0.5;
    lyricsOffset = Math.round(lyricsOffset * 10) / 10; // 保留一位小数
    toast("歌词偏移：" + (lyricsOffset >= 0 ? "+" : "") + lyricsOffset + "秒");
    // 强制重新同步（重置索引以跳过 idx===currentLyricIndex 的早退逻辑）
    currentLyricIndex = -1;
    syncLyrics(audio.currentTime);
  } else if (e.key === "t" || e.key === "T") {
    // T 键切换翻译显示
    e.preventDefault();
    toggleLyricsTranslate();
  } else if (e.key === "o" || e.key === "O") {
    // O 键打开偏移量面板
    e.preventDefault();
    toggleLyricsOffsetPanel();
  }
}

function toggleLyricsTranslate() {
  // 循环：原文 → 原文+翻译 → 仅翻译 → 原文
  const hasTranslation = lyricsData.some(l => l.translation);
  const hasRomaji = lyricsData.some(l => l.romaji);
  if (!hasTranslation && !hasRomaji) return;
  
  lyricsTranslateMode = (lyricsTranslateMode + 1) % 3;
  const modeNames = ["原文", "原文+翻译", "仅翻译"];
  toast(modeNames[lyricsTranslateMode]);
  renderLyrics();
  syncLyrics(audio.currentTime);
}

function toggleLyricsOffsetPanel() {
  const panel = _lyricsOffsetPanel;
  if (panel.style.display === "flex") {
    panel.style.display = "none";
  } else {
    if (_lyricsMoreMenu) _lyricsMoreMenu.style.display = "none";
    panel.style.display = "flex";
    updateOffsetPanelDisplay();
  }
}

function updateOffsetPanelDisplay() {
  _lyricsOffsetVal.textContent = (lyricsOffset >= 0 ? "+" : "") + lyricsOffset.toFixed(1) + "s";
}

function adjustLyricsOffset(delta) {
  lyricsOffset += delta;
  lyricsOffset = Math.round(lyricsOffset * 10) / 10;
  updateOffsetPanelDisplay();
  currentLyricIndex = -1; // 强制重新同步
  syncLyrics(audio.currentTime);
}

// ---- 歌词封面显示隐藏 ----
const _lyricsCoverWrap = $("lyrics-cover-wrap");
const _lyricsCoverToggleBtn = $("lyrics-cover-toggle-btn");
let lyricsCoverHidden = localStorage.getItem("lyrics-cover-hidden") === "1";

function applyLyricsCoverHidden() {
  if (!_lyricsCoverWrap) return;
  if (lyricsCoverHidden) {
    _lyricsCoverWrap.classList.add("hidden");
    if (_lyricsCoverToggleBtn) {
      _lyricsCoverToggleBtn.childNodes[_lyricsCoverToggleBtn.childNodes.length - 1].textContent = " 显示封面";
    }
  } else {
    _lyricsCoverWrap.classList.remove("hidden");
    if (_lyricsCoverToggleBtn) {
      _lyricsCoverToggleBtn.childNodes[_lyricsCoverToggleBtn.childNodes.length - 1].textContent = " 隐藏封面";
    }
  }
}

function toggleLyricsCover() {
  lyricsCoverHidden = !lyricsCoverHidden;
  localStorage.setItem("lyrics-cover-hidden", lyricsCoverHidden ? "1" : "0");
  applyLyricsCoverHidden();
}

// ---- 更多菜单 ----
const _lyricsMoreBtn = $("lyrics-more-btn");
const _lyricsMoreMenu = $("lyrics-more-menu");

function toggleLyricsMoreMenu() {
  if (!_lyricsMoreMenu) return;
  if (_lyricsMoreMenu.style.display === "flex") {
    _lyricsMoreMenu.style.display = "none";
  } else {
    // 关掉其他面板
    if (_lyricsOffsetPanel) _lyricsOffsetPanel.style.display = "none";
    if (_lyricsSearchPanel) _lyricsSearchPanel.style.display = "none";
    _lyricsMoreMenu.style.display = "flex";
  }
}

// 页面加载时应用封面设置
applyLyricsCoverHidden();

// ---- 歌词手动搜索 ----
function toggleLyricsSearchPanel() {
  const panel = _lyricsSearchPanel;
  const offsetPanel = _lyricsOffsetPanel;
  if (panel.style.display === "flex") {
    panel.style.display = "none";
  } else {
    // 关掉偏移面板和更多菜单
    if (offsetPanel) offsetPanel.style.display = "none";
    if (_lyricsMoreMenu) _lyricsMoreMenu.style.display = "none";
    panel.style.display = "flex";
    // 始终预填当前歌曲关键词
    if (_lyricsSearchInput) {
      _lyricsSearchInput.value = cleanLyricKeyword();
    }
    // 清空上次搜索结果
    if (_lyricsSearchResults) _lyricsSearchResults.innerHTML = "";
    setTimeout(() => {
      if (_lyricsSearchInput) {
        _lyricsSearchInput.focus();
        // 光标移到末尾
        const len = _lyricsSearchInput.value.length;
        _lyricsSearchInput.setSelectionRange(len, len);
      }
    }, 100);
  }
}

function cleanLyricKeyword() {
  // 从当前标题提取关键词（与后端 clean_keyword 对应）
  const raw = (_lyricsSongTitle.textContent || "").trim();
  if (!raw) return "";
  const m = raw.match(/《(.+?)》|「(.+?)」/);
  if (m) return (m[1] || m[2]).trim();
  return raw.replace(/【[^】]*】/g, "").replace(/"[^"]*"/g, "").trim();
}

async function searchLyrics() {
  const kw = (_lyricsSearchInput.value || "").trim();
  if (!kw) return;
  if (!_lyricsSearchResults) return;
  _lyricsSearchResults.innerHTML = '<div class="lyrics-search-loading">搜索中...</div>';
  try {
    const resp = await fetch(`/api/lyrics/search?keyword=${encodeURIComponent(kw)}&duration=${currentDuration || 0}`);
    const data = await resp.json();
    if (!data.ok || !data.results || data.results.length === 0) {
      _lyricsSearchResults.innerHTML = '<div class="lyrics-search-empty">没有找到结果，试试简化关键词</div>';
      return;
    }
    const sourceLabels = { netease: "网易云", qqmusic: "QQ音乐", lrclib: "lrclib" };
    _lyricsSearchResults.innerHTML = data.results.map(r => {
      const src = sourceLabels[r.source] || r.source;
      const durStr = r.duration > 0 ? ` | ${formatTime(r.duration)}` : "";
      return `<div class="lsr-item" data-source="${r.source}" data-id="${r.id}" onclick="pickLyricsResult('${r.source}','${r.id}')">
        <div class="lsr-info">
          <div class="lsr-title">${escapeHtml(r.title)}</div>
          <div class="lsr-meta">${escapeHtml(r.artist)}${durStr}</div>
        </div>
        <span class="lsr-tag">${src}</span>
      </div>`;
    }).join("");
  } catch (e) {
    _lyricsSearchResults.innerHTML = '<div class="lyrics-search-empty">搜索失败，请重试</div>';
  }
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = (s || "");
  return d.innerHTML;
}

async function pickLyricsResult(source, id) {
  if (!_lyricsSearchResults) return;
  // 高亮选中项
  _lyricsSearchResults.querySelectorAll(".lsr-item").forEach(el => el.classList.remove("lsr-picked"));
  const item = _lyricsSearchResults.querySelector(`.lsr-item[data-source="${source}"][data-id="${id}"]`);
  if (item) item.classList.add("lsr-picked");

  try {
    const resp = await fetch(`/api/lyrics/fetch?source=${encodeURIComponent(source)}&id=${encodeURIComponent(id)}`);
    const data = await resp.json();
    if (!data.ok || !data.lrc) {
      toast("获取歌词失败");
      return;
    }
    // 解析合并歌词
    const result = parseAndMergeLyrics(data.lrc, data.tlyric || "", data.romalrc || "");
    if (result && result.lines) {
      lyricsData = result.lines;
    } else if (Array.isArray(result)) {
      lyricsData = result;
    } else {
      lyricsData = [];
    }
    lyricsOffset = 0;
    currentLyricIndex = -1;
    lyricsTranslateMode = 0;
    updateOffsetPanelDisplay();
    renderLyrics();
    syncLyrics(audio.currentTime);
    // 关闭搜索面板并清空输入
    if (_lyricsSearchPanel) _lyricsSearchPanel.style.display = "none";
    if (_lyricsSearchInput) _lyricsSearchInput.value = "";
    toast("歌词已切换");

    // 回写缓存：下次播放同一首歌直接使用手动选择的歌词
    _saveLyricsPreference(data);
  } catch (e) {
    toast("请求失败");
  }
}

function _saveLyricsPreference(fetchedData) {
  // 将用户手动选择的歌词持久化到缓存
  const bvid = currentBvid || "";
  const title = (_lyricsSongTitle.textContent || "").trim();
  if (!bvid && !title) return;
  const cacheKey = bvid || title;
  fetch("/api/lyrics/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      bvid: bvid,
      title: title,
      lrc: fetchedData.lrc || "",
      tlyric: fetchedData.tlyric || "",
      romalrc: fetchedData.romalrc || "",
    })
  }).catch(() => {}); // 静默失败，不影响主流程
}

// 歌词页事件绑定（在 overlay 显示后绑定）
_lyricsOverlay?.addEventListener("click", (e) => {
  // 点击背景蒙层关闭
  if (e.target === _lyricsOverlay || e.target.closest(".lyrics-overlay-mask")) {
    closeLyrics();
  }
  // 点击歌词行跳转进度
  if (e.target.closest(".lyric-page-line")) {
    _onLyricLineClick(e);
  }
  // 点击搜索面板外部关闭
  if (_lyricsSearchPanel && _lyricsSearchPanel.style.display === "flex" && !e.target.closest("#lyrics-search-panel") && !e.target.closest("#lyrics-search-btn")) {
    _lyricsSearchPanel.style.display = "none";
  }
  // 点击更多菜单外部关闭
  if (_lyricsMoreMenu && _lyricsMoreMenu.style.display === "flex" && !e.target.closest("#lyrics-more-menu") && !e.target.closest("#lyrics-more-btn")) {
    _lyricsMoreMenu.style.display = "none";
  }
  // 点击偏移面板外部关闭
  if (_lyricsOffsetPanel && _lyricsOffsetPanel.style.display === "flex" && !e.target.closest("#lyrics-offset-panel") && !e.target.closest("#lyrics-offset-btn") && !e.target.closest("#lyrics-more-btn")) {
    _lyricsOffsetPanel.style.display = "none";
  }
});

// 歌词页鼠标移动 → 显示控制栏，3秒不动自动隐藏
_lyricsOverlay?.addEventListener("mousemove", () => {
  if (!lyricsOpen) return;
  showLyricsControls();
});

function showLyricsControls() {
  // 显示所有 UI 元素
  if (_lyricsControlBar) _lyricsControlBar.classList.add("visible");
  document.querySelectorAll(".lyrics-close, .lyrics-ctrls").forEach(el => el.classList.remove("lyrics-ui-hidden"));
  clearTimeout(lyricsControlTimer);
  lyricsControlTimer = setTimeout(() => {
    // 隐藏所有 UI 元素
    if (_lyricsControlBar) _lyricsControlBar.classList.remove("visible");
    document.querySelectorAll(".lyrics-close, .lyrics-ctrls").forEach(el => el.classList.add("lyrics-ui-hidden"));
  }, 3000);
}

function seekLyricsProgress(val) {
  if (!audio.duration) return;
  audio.currentTime = (val / 100) * audio.duration;
  seek(val);
}

// 歌词滚动区域：用户手动滚动时暂停自动跟随
_lyricsScroll?.addEventListener("wheel", () => {
  if (!lyricsOpen) return;
  _onLyricsUserScrollStart();
  // 在滚动停止后恢复（通过 debounce）
  clearTimeout(lyricsScrollTimer);
  lyricsScrollTimer = setTimeout(() => _onLyricsUserScrollEnd(), 2000);
}, { passive: true });

_lyricsScroll?.addEventListener("touchstart", () => {
  if (!lyricsOpen) return;
  _onLyricsUserScrollStart();
}, { passive: true });

_lyricsScroll?.addEventListener("touchend", () => {
  if (!lyricsOpen) return;
  clearTimeout(lyricsScrollTimer);
  lyricsScrollTimer = setTimeout(() => _onLyricsUserScrollEnd(), 2000);
}, { passive: true });

_lyricsScroll?.addEventListener("scroll", () => {
  if (!lyricsOpen || !lyricsIsUserScrolling) return;
  // 持续重置定时器
  clearTimeout(lyricsScrollTimer);
  lyricsScrollTimer = setTimeout(() => _onLyricsUserScrollEnd(), 2000);
}, { passive: true });

async function fetchLyrics(title, artist, bvid, duration) {
  lyricsData = [];
  currentLyricIndex = -1;
  if (!lyricsOpen) return;
  _lyricsScrollInner.innerHTML = '<div class="lyric-page-line lyric-page-loading">歌词加载中...</div>';
  try {
    const resp = await fetch(
      `/api/lyrics?title=${encodeURIComponent(title)}&artist=${encodeURIComponent(artist || "")}&bvid=${encodeURIComponent(bvid || "")}&duration=${duration || 0}`
    );
    const data = await resp.json();
    if (data.ok && data.lrc) {
      const result = parseAndMergeLyrics(data.lrc, data.tlyric || "", data.romalrc || "");
      if (result.lines) {
        lyricsData = result.lines;
      } else {
        // 兼容旧格式：result 本身就是行数组
        lyricsData = result;
      }
    }
  } catch (e) {
    // ignore
  }
  lyricsTranslateMode = 0;
  renderLyrics();
}



