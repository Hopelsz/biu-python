"""
BIU - HTML 模板
包含完整的 CSS 和 JavaScript 前端代码
"""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="referrer" content="no-referrer">
<title>BIU Music</title>
<style>
/* ========== 主题变量 ========== */
:root {
  --accent: #fb7299;
  --accent-hover: #fc8bab;
  --accent-light: #ff8cb3;
  --accent-active-text: #c9a0ff;
  --accent-active-bg: #2a2040;
  --accent-rgb: 251, 114, 153;

  --bg-body: #0f0f0f;
  --bg-titlebar: #151515;
  --bg-surface: #121212;
  --bg-surface-2: #141414;
  --bg-surface-3: #1a1a1a;
  --bg-surface-4: #1e1e1e;
  --bg-dropdown: #212121;
  --bg-hover: #222;
  --bg-hover-2: #252525;
  --bg-hover-3: #2a2a2a;
  --bg-element: #3a3a3a;

  --text-primary: #e0e0e0;
  --text-bright: #ddd;
  --text-secondary: #ccc;
  --text-dropdown: #bbb;
  --text-tertiary: #aaa;
  --text-muted: #888;
  --text-dim: #777;
  --text-dark: #666;
  --text-disabled: #555;
  --text-faint: #444;

  --color-danger: #e81123;
  --color-danger-text: #f55;
  --bg-danger: #3a1a1a;
  --color-white: #fff;
  --bg-toast: #333;
  --text-toast: #eee;
  --bg-overlay: rgba(0,0,0,.7);
  --shadow-sm: 0 4px 20px rgba(0,0,0,.6);
  --shadow-md: 0 8px 32px rgba(0,0,0,.6);
  --bg-scrollbar: #333;
  --bg-scrollbar-hover: #444;
  --bg-spinner-track: #333;
  --bg-progress-track: #3a3a3a;

  --accent-bg-10: rgba(251,114,153,0.1);
  --accent-bg-15: rgba(251,114,153,0.15);
  --accent-bg-20: rgba(251,114,153,0.2);
  --accent-bg-30: rgba(251,114,153,0.3);
  --accent-glow: rgba(251,114,153,.4);

  --icon-search: #555;
  --select-arrow-svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%23666'/%3E%3C/svg%3E");
}

/* 浅色主题 */
[data-theme="light"] {
  --accent: #4a90d9;
  --accent-hover: #5ea3e5;
  --accent-light: #7db8f0;
  --accent-active-text: #1a56b8;
  --accent-active-bg: #bbdefb;
  --accent-rgb: 74, 144, 217;

  --bg-body: #e2e6ec;
  --bg-titlebar: #f5f7fb;
  --bg-surface: #f9fbfd;
  --bg-surface-2: #f4f7fb;
  --bg-surface-3: #f1f4f9;
  --bg-surface-4: #e9edf3;
  --bg-dropdown: #f9fbfd;
  --bg-hover: #c5d2e3;
  --bg-hover-2: #b8c8dd;
  --bg-hover-3: #acbfd6;
  --bg-element: #dde5ed;

  --text-primary: #1a202c;
  --text-bright: #2d3748;
  --text-secondary: #2d3748;
  --text-dropdown: #4a5568;
  --text-tertiary: #4a5568;
  --text-muted: #718096;
  --text-dim: #718096;
  --text-dark: #a0aec0;
  --text-disabled: #a0aec0;
  --text-faint: #cbd5e0;

  --color-danger: #e53e3e;
  --color-danger-text: #c53030;
  --bg-danger: #fed7d7;
  --color-white: #fff;
  --bg-toast: #2d3748;
  --text-toast: #fff;
  --bg-overlay: rgba(0,0,0,.4);
  --shadow-sm: 0 4px 20px rgba(0,0,0,.08);
  --shadow-md: 0 8px 32px rgba(0,0,0,.12);
  --bg-scrollbar: #cbd5e0;
  --bg-scrollbar-hover: #a0aec0;
  --bg-spinner-track: #dde5ed;
  --bg-progress-track: #dde5ed;

  --accent-bg-10: rgba(74,144,217,0.08);
  --accent-bg-15: rgba(74,144,217,0.12);
  --accent-bg-20: rgba(74,144,217,0.18);
  --accent-bg-30: rgba(74,144,217,0.25);
  --accent-glow: rgba(74,144,217,.3);

  --icon-search: #a0aec0;
  --select-arrow-svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%23999'/%3E%3C/svg%3E");
}

* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg-body);
  color: var(--text-primary);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 自定义标题栏 */
.title-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 30px;
  padding: 0 10px;
  background: var(--bg-titlebar);
  flex-shrink: 0;
  user-select: none;
  cursor: default;
}
.title-bar .title-text {
  font-size: 13px;
  color: var(--accent);
  font-weight: 700;
  letter-spacing: .5px;
}
.title-bar .title-text .logo-icon { font-size: 16px; }
.title-bar .win-ctrl {
  display: flex;
  gap: 2px;
}
.title-bar .win-btn {
  width: 28px;
  height: 22px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  transition: all .1s;
  line-height: 1;
}
.title-bar .win-btn:hover { background: var(--bg-hover-3); color: var(--text-bright); }
.title-bar .win-btn.btn-close:hover { background: var(--color-danger); color: var(--color-white); }
.title-bar .theme-btn {
  width: 28px; height: 22px; border: none;
  background: transparent; color: var(--text-muted);
  cursor: pointer; display: flex;
  align-items: center; justify-content: center;
  border-radius: 4px; transition: all .15s ease;
  margin-right: 2px; padding: 0;
}
.title-bar .theme-btn:hover { background: var(--bg-hover-3); color: var(--accent); }
.title-bar .theme-btn svg {
  width: 16px; height: 16px;
  transition: transform .35s cubic-bezier(.4,0,.2,1), opacity .2s ease;
}
.theme-btn .icon-moon { display: block; }
.theme-btn .icon-sun  { display: none; }
[data-theme="light"] .theme-btn .icon-moon { display: none; }
[data-theme="light"] .theme-btn .icon-sun  { display: block; }
.title-bar .theme-btn:active svg { transform: rotate(60deg); }

/* 顶部栏 - 紧凑 */
.header {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px 7px;
  background: var(--bg-surface);
  flex-shrink: 0;
  position: relative;
}
.header-top-right { position: absolute; right: 12px; display: flex; align-items: center; gap: 8px; }
.search-wrap {
  flex: 1;
  max-width: 180px;
  position: relative;
}
.search-wrap svg {
  position: absolute;
  left: 9px;
  top: 50%;
  transform: translateY(-50%);
  width: 13px; height: 13px;
  color: var(--icon-search);
  pointer-events: none;
}
.header-search {
  width: 100%;
  padding: 5px 26px 5px 28px;
  border: none;
  border-radius: 14px;
  background: var(--bg-surface-4);
  color: var(--text-secondary);
  font-size: 11px;
  outline: none;
  transition: background .2s;
  box-sizing: border-box;
}
.header-search:focus { background: var(--bg-hover-2); }
.header-search::placeholder { color: var(--text-disabled); }
.search-clear {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px; height: 14px;
  border: none;
  background: none;
  color: var(--text-disabled);
  cursor: pointer;
  font-size: 12px;
  line-height: 14px;
  text-align: center;
  padding: 0;
  border-radius: 50%;
  display: none;
}
.search-clear:hover { color: var(--text-secondary); background: var(--bg-hover); }
.search-clear.visible { display: block; }
.user-avatar {
  width: 24px; height: 24px;
  border-radius: 50%;
  flex-shrink: 0;
  cursor: pointer;
  object-fit: cover;
}
.user-avatar:hover { opacity: .85; }
.btn-login {
  width: 24px; height: 24px;
  border-radius: 50%;
  background: var(--bg-surface-4);
  color: var(--text-muted);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  padding: 0;
  flex-shrink: 0;
  border: none;
}
.btn-login:hover { background: var(--bg-hover-3); color: var(--accent); }
/* 头像下拉菜单 */
.avatar-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 6px;
  background: var(--bg-dropdown);
  border-radius: 8px;
  padding: 4px 0;
  min-width: 120px;
  z-index: 150;
  display: none;
  box-shadow: var(--shadow-sm);
}
.avatar-dropdown.show { display: block; }
.avatar-dropdown .dd-item {
  padding: 6px 14px;
  font-size: 12px;
  color: var(--text-dropdown);
  cursor: pointer;
  display: block;
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  transition: background .1s;
}
.avatar-dropdown .dd-item:hover { background: var(--bg-hover-3); color: var(--color-white); }
.avatar-dropdown .dd-item.danger:hover { background: var(--bg-danger); color: var(--color-danger-text); }
.btn {
  padding: 4px 10px;
  border: none;
  border-radius: 5px;
  background: var(--bg-hover-3);
  color: var(--text-bright);
  cursor: pointer;
  font-size: 11px;
  transition: all .15s;
}
.btn:hover { background: var(--bg-element); }
.btn-primary { background: var(--accent); color: var(--color-white); }
.btn-primary:hover { background: var(--accent-hover); }
.btn-sm { padding: 3px 8px; font-size: 11px; }
.link-accent { color: var(--accent); text-decoration: none; }
.link-accent:hover { text-decoration: underline; }

/* Cookie 弹窗 */
.overlay {
  position: fixed; inset: 0;
  background: var(--bg-overlay);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
}
.dialog {
  background: var(--bg-surface-4);
  border-radius: 12px;
  padding: 24px;
  width: 320px;
  max-width: 90vw;
  box-shadow: var(--shadow-md);
}
.dialog h2 { font-size: 16px; margin-bottom: 12px; }
.dialog p { font-size: 12px; color: var(--text-muted); margin-bottom: 12px; line-height: 1.6; }
.dialog input {
  width: 100%; padding: 10px;
  border: none;
  border-radius: 6px;
  background: var(--bg-surface);
  color: var(--text-bright);
  font-size: 13px;
  margin-bottom: 12px;
  outline: none;
}
.dialog .actions { display: flex; gap: 8px; justify-content: flex-end; }

/* 设置页面 */
.settings-page {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.settings-page-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 4px;
}
.settings-page-header .back-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
  padding: 2px 4px;
  border-radius: 4px;
}
.settings-page-header .back-btn:hover { color: var(--accent); }
.settings-tabs {
  display: flex;
  gap: 0;
  margin: 0 -12px 12px -12px;
  padding: 0 12px;
}
.settings-tab {
  background: none;
  border: none;
  color: var(--text-dim);
  padding: 8px 16px;
  cursor: pointer;
  font-size: 12px;
  position: relative;
}
.settings-tab:hover { color: var(--text-tertiary); }
.settings-tab.active { color: var(--accent); }
.settings-tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent);
}
.settings-section {
  margin-bottom: 20px;
}
.settings-section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 2px;
}
.settings-section-desc {
  font-size: 10px;
  color: var(--text-dark);
  margin-bottom: 8px;
}
.settings-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
}
.settings-label {
  font-size: 12px;
  color: var(--text-tertiary);
  white-space: nowrap;
  margin-right: 16px;
}
.settings-row select {
  flex: 1;
  padding: 6px 8px;
  background: var(--bg-surface-4);
  border: none;
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  background-image: var(--select-arrow-svg);
  background-repeat: no-repeat;
  background-position: right 8px center;
  padding-right: 28px;
}
.settings-row select:hover { background: var(--bg-hover-2); }
.settings-row select:focus { background: var(--bg-hover-2); }
.settings-preview {
  margin-top: 12px;
  padding: 10px 12px;
  background: var(--bg-surface-3);
  border-radius: 6px;
}
.settings-preview .preview-label {
  font-size: 10px;
  color: var(--text-disabled);
  margin-bottom: 4px;
}
.settings-preview .preview-text {
  color: var(--text-tertiary);
  line-height: 1.5;
}
.settings-check-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.settings-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-tertiary);
  background: var(--bg-surface-3);
  transition: background 0.15s;
}
.settings-item:hover { background: var(--bg-hover-2); }
.settings-item input[type="checkbox"] {
  width: 14px; height: 14px;
  accent-color: var(--accent);
  cursor: pointer;
  margin: 0;
}
.settings-item .s-name { max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.settings-item .s-count { color: var(--text-disabled); font-size: 12px; flex-shrink: 0; }

/* 主体 - 收藏夹列表占满 */
.main {
  flex: 1;
  overflow: hidden;
  position: relative;
}
.folder-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  padding: 0 0 2px 0;
}
.folder-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background .15s, border-color .2s;
  border: none;
  border-left: 3px solid transparent;
  background: none;
  color: var(--text-secondary);
  width: 100%;
  text-align: left;
  font-size: 13px;
  position: relative;
}
.folder-item:hover { background: var(--bg-hover); border-left-color: var(--accent); }
.folder-item.active { background: var(--accent-active-bg); color: var(--accent-active-text); border-left-color: var(--accent-active-text); }
.folder-list.no-results .folder-item { pointer-events: none; opacity: 0.35; }
.folder-item.locate-flash {
  animation: locatePulse 0.4s ease-in-out 3;
  border-left-color: var(--accent) !important;
}
@keyframes locatePulse {
  0%, 100% { box-shadow: inset 0 0 0 transparent; }
  50% { box-shadow: inset 0 0 30px var(--accent-glow); }
}
.folder-item .folder-cover { width: 24px; height: 24px; border-radius: 3px; object-fit: cover; flex-shrink: 0; }
.folder-item .folder-cover-placeholder {
  width: 24px; height: 24px; border-radius: 3px; flex-shrink: 0;
  background: var(--bg-hover);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px;
}
.folder-item .folder-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
.folder-item .folder-count { font-size: 11px; color: var(--text-disabled); flex-shrink: 0; }
.folder-item .arrow {
  font-size: 11px;
  color: var(--text-disabled);
  flex-shrink: 0;
  transition: color .15s, transform .15s;
}
.folder-item:hover .arrow { color: var(--accent); }
.folder-item.expanded .arrow { color: var(--accent); transform: translateX(2px); }
.folder-item.expanded {
  position: sticky;
  top: 0;
  z-index: 5;
  background: var(--bg-surface-2);
}
.folder-item.active.expanded {
  background: var(--accent-active-bg);
  color: var(--accent-active-text);
}

/* 折叠面板 - 收藏夹内容 */
.folder-content {
  display: none;
  background: var(--bg-surface-2);
  margin: 0 0 2px 0;
  padding: 0;
  overflow: hidden;
  transition: max-height .25s ease;
}
.folder-content.expanded { display: block; overflow-y: auto; }
.fc-song-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  transition: background .1s;
  font-size: 12px;
  border-left: 3px solid transparent;
}
.fc-song-item:hover { background: var(--bg-hover); }
.fc-song-item.playing {
  background: var(--accent-active-bg);
  border-left-color: var(--accent);
  color: var(--accent-active-text);
}
.fc-song-item .idx { color: var(--text-disabled); font-size: 10px; width: 20px; text-align: center; flex-shrink: 0; }
.fc-song-item.playing .idx { color: var(--accent); font-weight: 600; }
.fc-song-item .s-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}
.fc-song-item .s-meta { font-size: 10px; color: var(--text-disabled); flex-shrink: 0; }
.fc-song-item .s-dur { font-size: 10px; color: var(--text-faint); flex-shrink: 0; }

.fc-more { text-align: center; padding: 6px; }
.fc-more button {
  background: var(--bg-hover-3); color: var(--text-tertiary); border: none;
  padding: 4px 14px; border-radius: 4px; cursor: pointer; font-size: 11px;
}
.fc-more button:hover { background: var(--bg-element); color: var(--text-bright); }
.fc-empty { text-align: center; padding: 16px; color: var(--text-disabled); font-size: 12px; }



.loading, .empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-disabled);
  font-size: 13px;
  gap: 8px;
}
.spinner {
  width: 16px; height: 16px;
  border: 2px solid var(--bg-spinner-track);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.hidden-hint {
  text-align: center;
  color: var(--text-disabled);
  font-size: 11px;
  padding: 8px;
  cursor: pointer;
  transition: color 0.15s;
}
.hidden-hint:hover { color: var(--accent); }

#content-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* 底部播放器 */
.player {
  background: var(--bg-surface);
  padding: 6px 10px 8px;
  flex-shrink: 0;
}
.player-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.player-info .title {
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  color: var(--text-bright);
}
.folder-src {
  font-size: 10px;
  color: var(--accent);
  cursor: pointer;
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 8px;
  background: var(--accent-bg-10);
  white-space: nowrap;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background 0.15s;
}
.folder-src:hover { background: var(--accent-bg-20); text-decoration: underline; }


.progress-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.progress-wrap span { font-size: 10px; color: var(--text-dark); flex-shrink: 0; min-width: 28px; }
.progress-wrap span:last-child { text-align: right; }
.progress-wrap input[type="range"] {
  flex: 1;
  -webkit-appearance: none;
  height: 5px;
  background: var(--bg-progress-track);
  border-radius: 3px;
  cursor: pointer;
}
.progress-wrap input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  box-shadow: 0 0 6px var(--accent-glow);
}
.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.ctrl-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 16px;
  padding: 3px 4px;
  border-radius: 4px;
  transition: all .15s;
  line-height: 1;
  flex-shrink: 0;
}
.ctrl-btn:hover { color: var(--color-white); background: var(--bg-hover-3); }
.ctrl-btn.play-btn { font-size: 20px; color: var(--accent); }
.ctrl-btn.play-btn:hover { color: var(--accent-hover); background: var(--accent-bg-10); }
.ctrl-btn.mode-btn {
  font-size: 13px;
  color: var(--text-dim);
  padding: 3px 5px;
  position: relative;
}
.ctrl-btn.mode-btn:hover { color: var(--accent); }
.ctrl-btn.mode-btn.loop-one::after {
  content: "1"; position: absolute;
  font-size: 7px; font-weight: 700;
  top: 1px; right: 2px;
  color: var(--accent);
}

.volume-wrap {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  position: relative;
}
.volume-wrap span { font-size: 14px; color: var(--text-muted); cursor: pointer; }
.vol-tip {
  position: absolute;
  top: -18px;
  background: var(--accent);
  color: var(--color-white);
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
  pointer-events: none;
  opacity: 0;
  transition: opacity .15s;
  line-height: 1.4;
  white-space: nowrap;
  transform: translateX(-50%);
}
.vol-tip.show { opacity: 1; }
.volume-wrap input[type="range"] {
  width: 48px;
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  background: linear-gradient(to right, var(--accent) 0%, var(--accent) 10%, var(--bg-progress-track) 10%, var(--bg-progress-track) 100%);
  border-radius: 2px;
  cursor: pointer;
}
.volume-wrap input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
}
.volume-wrap input[type="range"]::-webkit-slider-thumb:hover { background: var(--accent-light); }

/* toast */
.toast {
  position: fixed; bottom: 80px; left: 50%;
  transform: translateX(-50%);
  background: var(--bg-toast);
  color: var(--text-toast);
  padding: 6px 16px;
  border-radius: 16px;
  font-size: 12px;
  z-index: 300;
  opacity: 0;
  transition: opacity .3s;
  pointer-events: none;
  white-space: nowrap;
}
.toast.show { opacity: 1; }

/* 滚动条 */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--bg-scrollbar); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--bg-scrollbar-hover); }
</style>
</head>
<body data-theme="dark">

<!-- Cookie 弹窗 -->
<div id="cookie-dialog" class="overlay" style="display:none">
  <div class="dialog">
    <h2>登录 Bilibili</h2>
    <p>1. 打开 <a href="https://www.bilibili.com" target="_blank" class="link-accent">bilibili.com</a> 并登录<br>
    2. 按 F12 → Application → Cookies → 复制 <b>SESSDATA</b> 的值<br>
    3. 粘贴到下方：</p>
    <input id="sessdata-input" type="text" placeholder="粘贴 SESSDATA...">
    <div class="actions">
      <button class="btn" onclick="hideCookieDialog()">取消</button>
      <button class="btn btn-primary" onclick="saveCookie()">确认登录</button>
    </div>
  </div>
</div>

<div id="toast" class="toast"></div>



<!-- 自定义标题栏 -->
<div class="title-bar">
  <span class="title-text"><span class="logo-icon">♫</span>BIU</span>
  <div style="display:flex;align-items:center;gap:2px;">
    <button class="theme-btn" id="theme-toggle-btn" title="切换浅色模式">
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <svg class="icon-sun"  viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
    </button>
    <div class="win-ctrl">
      <button class="win-btn" onclick="window.pywebview.api.minimize()" title="最小化">─</button>
      <button class="win-btn btn-close" onclick="window.pywebview.api.close()" title="关闭">✕</button>
    </div>
  </div>
</div>


<div id="content-wrap">
<!-- 顶部 -->
<div class="header">
  <div class="search-wrap">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <input class="header-search" id="header-search" type="text" placeholder="搜索歌曲..." oninput="filterSongs();toggleSearchClear()">
    <button class="search-clear" id="search-clear" onclick="clearSearch()" title="清空">✕</button>
  </div>
  <div class="header-top-right">
    <img id="user-avatar" class="user-avatar" src="" alt="" style="display:none" title="" onclick="toggleAvatarMenu(event)">
    <div class="avatar-dropdown" id="avatar-dropdown">
      <button class="dd-item" onclick="showSettings();document.getElementById('avatar-dropdown').classList.remove('show')">设置</button>
      <button class="dd-item danger" onclick="logout()">退出登录</button>
    </div>
    <button class="btn-login" id="login-btn" onclick="showCookieDialog()" title="登录">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="display:block">
        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
      </svg>
    </button>
  </div>
</div>

<!-- 设置页面 -->
<div class="settings-page" id="settings-page" style="display:none">
  <div class="settings-page-header">
    <button class="back-btn" onclick="hideSettings()">← 返回</button>
  </div>
  <div class="settings-tabs">
    <button class="settings-tab active" data-tab="display" onclick="switchSettingsTab('display', this)">显示设置</button>
    <button class="settings-tab" data-tab="system" onclick="switchSettingsTab('system', this)">系统设置</button>
  </div>
  <div class="settings-section" data-tab-content="display">
    <div class="settings-section-title">收藏夹显示</div>
    <div class="settings-section-desc">勾选要在列表中显示的收藏夹</div>
    <div class="settings-check-list" id="settings-check-list"></div>
    <div style="margin-top:8px;display:flex;gap:6px;">
      <button class="btn btn-sm" onclick="toggleAllCheckboxes()">全不选</button>
      <button class="btn btn-primary btn-sm" onclick="saveSettings()">保存</button>
    </div>
  </div>
  <div class="settings-section" data-tab-content="system" style="display:none">
    <div class="settings-section-title">外观</div>
    <div class="settings-section-desc">调整界面字体与大小</div>
    <div class="settings-row">
      <span class="settings-label">字体</span>
      <select id="sys-font-family">
        <option value="default">系统默认</option>
        <option value="noto-sans">Noto Sans SC</option>
        <option value="noto-serif">Noto Serif SC</option>
        <option value="wenkai">霞鹜文楷</option>
        <option value="xiaowei">站酷小薇</option>
        <option value="mono">等宽字体</option>
      </select>
    </div>
    <div class="settings-preview" id="font-preview">
      <div class="preview-label">预览</div>
      <div class="preview-text">ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>abcdefghijklmnopqrstuvwxyz<br>0123456789 · 天地玄黄 宇宙洪荒</div>
    </div>
    <div style="margin-top:8px;">
      <button class="btn btn-primary btn-sm" onclick="saveSystemSettings()">保存</button>
    </div>
  </div>
</div>

<!-- 主体 - 文件夹列表 -->
<div class="main" id="main-area">
  <div class="folder-list" id="folder-list">
    <div class="empty">加载中...</div>
  </div>
</div>
</div>

<!-- 底部播放器 -->
<div class="player">
  <div class="player-info">
    <span class="title" id="now-title">♫ 未在播放</span>
    <span class="folder-src" id="folder-src" style="display:none" onclick="locateCurrentFolder()" title="点击定位收藏夹"></span>
  </div>
  <div class="progress-wrap">
    <span id="cur-time">0:00</span>
    <input type="range" id="progress" min="0" max="100" value="0" oninput="seek(this.value)">
    <span id="dur-time">0:00</span>
  </div>
  <div class="controls">
    <button class="ctrl-btn mode-btn" onclick="togglePlayMode()" id="btn-mode" title="列表循环">🔁</button>
    <button class="ctrl-btn" onclick="prevSong()" id="btn-prev" title="上一首">⏮</button>
    <button class="ctrl-btn play-btn" onclick="togglePlay()" id="btn-play" title="播放/暂停">▶</button>
    <button class="ctrl-btn" onclick="nextSong()" id="btn-next" title="下一首">⏭</button>
    <div class="volume-wrap">
      <span onclick="toggleMute()" id="vol-icon">🔊</span>
      <input type="range" id="volume" min="0" max="100" value="10"
             oninput="setVolume(this.value)" onchange="hideVolTip()">
      <div class="vol-tip" id="vol-tip">10</div>
    </div>
  </div>
</div>

<audio id="audio" preload="auto" style="display:none"></audio>

<script>
// ---- 窗口拖拽 ----
(function() {
  const titleBar = document.querySelector(".title-bar");
  let dragging = false, offsetX = 0, offsetY = 0;

  titleBar.addEventListener("mousedown", (e) => {
    if (e.target.closest(".win-btn")) return; // 不拦截按钮点击
    dragging = true;
    offsetX = e.screenX - window.screenX;
    offsetY = e.screenY - window.screenY;
    titleBar.style.cursor = "grabbing";
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
      titleBar.style.cursor = "default";
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

const audio = document.getElementById("audio");
audio.volume = 0.1;

// ---- Cookie ----
function showCookieDialog() {
  document.getElementById("cookie-dialog").style.display = "flex";
}
function hideCookieDialog() {
  document.getElementById("cookie-dialog").style.display = "none";
}
async function saveCookie() {
  const val = document.getElementById("sessdata-input").value.trim();
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
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 2000);
}

// ---- 用户信息 ----
async function loadUser() {
  const resp = await fetch("/api/user");
  const data = await resp.json();
  const avatarEl = document.getElementById("user-avatar");
  const loginBtn = document.getElementById("login-btn");
  if (data.logged_in) {
    const uname = data.uname || ("UID:" + data.mid);
    loginBtn.style.display = "none";
    if (data.face) {
      avatarEl.src = data.face;
      avatarEl.title = uname;
      avatarEl.style.display = "block";
    }
    document.getElementById("header-search").placeholder = "搜索歌曲...";
  } else {
    loginBtn.style.display = "";
    avatarEl.style.display = "none";
  }
  return data;
}

function toggleAvatarMenu(e) {
  e.stopPropagation();
  document.getElementById("avatar-dropdown").classList.toggle("show");
}

document.addEventListener("click", () => {
  document.getElementById("avatar-dropdown").classList.remove("show");
});

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
  const list = document.getElementById("folder-list");
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
        const placeholder = document.querySelector(`.folder-cover-placeholder[data-mid="${f.id}"]`);
        if (placeholder) {
          placeholder.outerHTML = `<img class="folder-cover" src="${esc(info.cover)}" onerror="this.replaceWith(document.createTextNode('📁'))" />`;
        }
      }
    } catch(e) { /* 封面加载失败，保留占位符 */ }
  }
}

// ---- 设置页面 ----
function showSettings() {
  const list = document.getElementById("settings-check-list");
  list.innerHTML = folders.map(f => {
    const checked = !hiddenFolders.includes(f.id);
    return `<label class="settings-item">
      <input type="checkbox" data-fid="${f.id}" ${checked ? "checked" : ""}>
      <span class="s-name">${esc(f.title)}</span>
      <span class="s-count">${f.count}首</span>
    </label>`;
  }).join("");
  document.getElementById("main-area").style.display = "none";
  document.getElementById("settings-page").style.display = "block";
  loadSystemSettings();
}

function hideSettings() {
  document.getElementById("settings-page").style.display = "none";
  document.getElementById("main-area").style.display = "";
}

function switchSettingsTab(tabName, el) {
  document.querySelectorAll(".settings-tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".settings-section[data-tab-content]").forEach(s => s.style.display = "none");
  el.classList.add("active");
  const panel = document.querySelector(`.settings-section[data-tab-content="${tabName}"]`);
  if (panel) panel.style.display = "block";
}

async function saveSettings() {
  const checks = document.querySelectorAll("#settings-check-list input[type=checkbox]");
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
    document.getElementById("sys-font-family").value = ff;
    applyFontSettings(ff);
    applyTheme(theme);
  } catch(e) {}
}

function applyTheme(theme) {
  document.body.setAttribute("data-theme", theme);
  const btn = document.getElementById("theme-toggle-btn");
  if (btn) {
    btn.title = theme === "light" ? "切换深色模式" : "切换浅色模式";
  }
}

function applyFontSettings(ff) {
  const family = FONT_FAMILIES[ff] || FONT_FAMILIES["default"];
  document.body.style.fontFamily = family;
  // 预览
  const preview = document.getElementById("font-preview");
  if (preview) {
    preview.querySelector(".preview-text").style.fontFamily = family;
    preview.querySelector(".preview-text").style.fontSize = "14px";
  }
}

document.getElementById("sys-font-family").addEventListener("change", function() {
  applyFontSettings(this.value);
});
document.getElementById("theme-toggle-btn").addEventListener("click", function() {
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
  const ff = document.getElementById("sys-font-family").value;
  const theme = document.body.getAttribute("data-theme") || "dark";
  try {
    await fetch("/api/system-settings", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({font_family: ff, theme: theme})
    });
    applyFontSettings(ff);
    toast("设置已保存");
  } catch(e) {
    toast("保存失败");
  }
}

function toggleAllCheckboxes() {
  const checks = document.querySelectorAll("#settings-check-list input[type=checkbox]");
  const allChecked = Array.from(checks).every(cb => cb.checked);
  checks.forEach(cb => { cb.checked = !allChecked; });
  const btn = event.target;
  btn.textContent = allChecked ? "全选" : "全不选";
}

// ---- 播放模式 ----
function togglePlayMode() {
  playMode = (playMode + 1) % 3;
  const btn = document.getElementById("btn-mode");
  btn.textContent = MODE_ICONS[playMode];
  btn.title = MODE_TITLES[playMode];
  btn.classList.toggle("loop-one", playMode === 1);
}

// ---- 折叠面板：点击展开/收起收藏夹内容 ----
let folderContents = {}; // { media_id: { items:[], hasMore:bool, page:int, title:str } }

function collapseAll() {
  document.querySelectorAll(".folder-content.expanded").forEach(el => {
    el.classList.remove("expanded");
  });
  document.querySelectorAll(".folder-item.expanded").forEach(el => el.classList.remove("expanded"));
  document.querySelectorAll(".folder-wrap.expanded").forEach(el => el.classList.remove("expanded"));
  document.querySelectorAll(".folder-item .arrow").forEach(el => el.textContent = "▶");
}

function toggleFolder(idx) {
  const folder = folders[idx];
  if (!folder) return;

  const itemEl = document.querySelector(`.folder-item[data-idx="${idx}"]`);
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
  document.querySelectorAll(".folder-item").forEach(el => el.classList.remove("active"));
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
  } catch(e) {
    container.innerHTML = '<div class="fc-empty">加载失败</div>';
    container.dataset.loaded = "1";
  }
}

function renderFolderContent(mediaId, container) {
  const data = folderContents[mediaId];
  if (!data) return;

  let html = '<div class="fc-songs">';

  data.items.forEach((s, i) => {
    if (s.type !== 2) return;
    const dur = s.duration ? formatTime(s.duration) : "";
    const isPlaying = i === currentIndex && playbackFolder && playbackFolder.id == mediaId;
    html += `<div class="fc-song-item${isPlaying ? " playing" : ""}"
                  data-idx="${i}" data-bvid="${esc(s.bvid||'')}"
                  onclick="playFolderSong(${i}, '${mediaId}')">
      <span class="idx">${i + 1}</span>
      <span class="s-title">${esc(s.title)}</span>
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

  const btn = document.querySelector(`#fc-more-btn-${mediaId}`);
  if (btn) btn.textContent = "加载中...";

  const resp = await fetch(`/api/folder-content?media_id=${mediaId}&page=${nextPage}`);
  const result = await resp.json();
  const newItems = result.items || [];

  data.items = data.items.concat(newItems);
  data.hasMore = result.has_more || false;
  data.page = nextPage;

  const container = document.querySelector(`.folder-content[data-mid="${mediaId}"]`);
  if (container) renderFolderContent(mediaId, container);
}

function toggleSearchClear() {
  const input = document.getElementById("header-search");
  const btn = document.getElementById("search-clear");
  if (input.value.trim()) {
    btn.classList.add("visible");
  } else {
    btn.classList.remove("visible");
  }
}
function clearSearch() {
  const input = document.getElementById("header-search");
  input.value = "";
  input.focus();
  toggleSearchClear();
  filterSongs();
}

async function filterSongs() {
  const q = document.getElementById("header-search").value.trim().toLowerCase();
  const expanded = document.querySelector(".folder-item.expanded");

  // 没有展开的收藏夹 → 搜索不生效
  if (!expanded) {
    document.getElementById("folder-list").classList.remove("no-results");
    return;
  }

  const mediaId = expanded.dataset.id;

  // 清空搜索 → 恢复当前收藏夹完整列表
  if (!q) {
    filterSongsInFolder(mediaId, "");
    document.getElementById("folder-list").classList.remove("no-results");
    return;
  }

  // 在当前收藏夹内搜索
  const matchCount = filterSongsInFolder(mediaId, q);
  if (matchCount > 0) {
    document.getElementById("folder-list").classList.remove("no-results");
  } else {
    document.getElementById("folder-list").classList.add("no-results");
  }
}


function filterSongsInFolder(mediaId, q) {
  const data = folderContents[mediaId];
  if (!data) return 0;

  const container = document.querySelector(`.folder-content[data-mid="${mediaId}"]`);
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
  document.querySelectorAll(".folder-item").forEach(el => el.classList.remove("active"));
  const folderItem = document.querySelector(`.folder-item[data-id="${mediaId}"]`);
  if (folderItem) folderItem.classList.add("active");

  // 更新底部来源标签
  const srcEl = document.getElementById("folder-src");
  srcEl.textContent = "📁 " + (data.title || "收藏夹");
  srcEl.style.display = "inline";

  // 高亮当前播放曲目
  document.querySelectorAll(".fc-song-item").forEach(el => el.classList.remove("playing"));
  const songEl = document.querySelector(`.folder-content[data-mid="${mediaId}"] .fc-song-item[data-idx="${idx}"]`);
  if (songEl) {
    songEl.classList.add("playing");
    songEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  playBvidSong(song.bvid, song.title);
}

// ---- 播放 ----
function playBvidSong(bvid, title) {
  document.getElementById("now-title").textContent = "⏳ " + title;
  // 记录当前歌曲的来源收藏夹（此后不受悬浮影响）
  playbackFolder = currentFolder ? { id: currentFolder.id, title: currentFolder.title } : null;
  // 显示来源收藏夹
  const srcEl = document.getElementById("folder-src");
  if (playbackFolder && playbackFolder.title) {
    srcEl.textContent = "📁 " + playbackFolder.title;
    srcEl.style.display = "inline";
  } else {
    srcEl.style.display = "none";
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

  const folderEl = document.querySelector(`.folder-item[data-id="${folder.id}"]`);
  if (!folderEl) {
    toast("收藏夹不在当前列表中");
    return;
  }

  // 滚动到目标收藏夹
  folderEl.scrollIntoView({ behavior: "smooth", block: "center" });

  // 高亮 + 闪烁
  document.querySelectorAll(".folder-item").forEach(el => el.classList.remove("active"));
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
  document.getElementById("progress").style.background = `linear-gradient(to right, ${acc} 0%, ${acc} ${val}%, ${trk} ${val}%, ${trk} 100%)`;
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
  document.getElementById("volume").value = val;
  updateVolSlider(val);
  updateVolIcon();
}

function updateVolSlider(val) {
  const pct = val || audio.volume * 100;
  const slider = document.getElementById("volume");
  const acc = themeVar('--accent'), trk = themeVar('--bg-progress-track');
  slider.style.background = `linear-gradient(to right, ${acc} 0%, ${acc} ${pct}%, ${trk} ${pct}%, ${trk} 100%)`;
}

function showVolTip(val) {
  const tip = document.getElementById("vol-tip");
  tip.textContent = Math.round(val);
  // 计算滑块小球位置：icon宽度(~24px) + gap(2px) + 滑块48px * 百分比
  const iconW = 26;
  const sliderW = 48;
  tip.style.left = (iconW + sliderW * (val / 100)) + "px";
  tip.classList.add("show");
  clearTimeout(tip._t);
  tip._t = setTimeout(() => tip.classList.remove("show"), 800);
}

function hideVolTip() {
  const tip = document.getElementById("vol-tip");
  clearTimeout(tip._t);
  tip.classList.remove("show");
}

function updateVolIcon() {
  const icon = document.getElementById("vol-icon");
  if (audio.volume === 0) icon.textContent = "🔇";
  else if (audio.volume < 0.5) icon.textContent = "🔉";
  else icon.textContent = "🔊";
}

function updatePlayUI() {
  const btn = document.getElementById("btn-play");
  btn.textContent = isPlaying ? "⏸" : "▶";
}


// ---- 音频事件 ----
audio.addEventListener("timeupdate", () => {
  if (!audio.duration) return;
  const pct = (audio.currentTime / audio.duration) * 100;
  const progress = document.getElementById("progress");
  progress.value = pct;
  const acc = themeVar('--accent'), trk = themeVar('--bg-progress-track');
  progress.style.background = `linear-gradient(to right, ${acc} 0%, ${acc} ${pct}%, ${trk} ${pct}%, ${trk} 100%)`;
  document.getElementById("cur-time").textContent = formatTime(audio.currentTime);
});

audio.addEventListener("loadedmetadata", () => {
  document.getElementById("dur-time").textContent = formatTime(audio.duration);
  document.getElementById("progress").style.background = themeVar('--bg-progress-track');
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
  const titleEl = document.getElementById("now-title");
  let title = titleEl ? titleEl.textContent : "未在播放";
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
  const data = await loadUser();
  if (data.logged_in) {
    await loadHiddenFolders();
    await loadFolders();
  } else {
    document.getElementById("folder-list").innerHTML = '<div class="empty">请点击右上角登录</div>';
  }
})();
</script>
</body>
</html>"""
