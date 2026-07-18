/* BIU - Settings Page Functions */
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
