"""
BIU - 轻量级 Bilibili 音乐播放器
Python + Flask + pywebview 桌面版
"""
import json
import logging
import os
import re
import sys
import threading
import time

import webview
from flask import Flask

from bilibili import BiliClient
from routes import WindowApi, register_routes

# ---- 应用路径 & 日志 ----
def _get_app_dir() -> str:
    """获取应用目录（兼容 PyInstaller 打包）"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# ---- Flask 应用 ----
app = Flask(__name__)

CONFIG_FILE = os.path.join(_get_app_dir(), "config.json")
client = BiliClient()


# ---- 配置读写 ----
def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ---- 启动时加载 cookie ----
cfg = load_config()
if cfg.get("sessdata"):
    client.set_cookie(cfg["sessdata"])
if cfg.get("buvid"):
    client._buvid = cfg["buvid"]

# ---- 注册路由 ----
register_routes(app, client, load_config, save_config)


# ---- 系统托盘 ----
def _get_tray_image(app_dir: str):
    """加载托盘图标，优先使用 BIU.ico"""
    from PIL import Image

    # PyInstaller 打包后图标在 _MEIPASS 内，未打包时在 app_dir 内
    if getattr(sys, "frozen", False):
        ico_path = os.path.join(sys._MEIPASS, "BIU.ico")
    else:
        ico_path = os.path.join(app_dir, "BIU.ico")

    if os.path.exists(ico_path):
        try:
            img = Image.open(ico_path)
            img = img.convert("RGBA")           # 确保有透明通道
            img = img.resize((32, 32), Image.LANCZOS)  # 缩小到托盘尺寸，高质量采样
            return img
        except Exception:
            pass

    # 兜底：生成简单音乐图标
    from PIL import ImageDraw

    img = Image.new("RGBA", (64, 64), (108, 92, 231, 255))
    draw = ImageDraw.Draw(img)
    draw.text((18, 12), "♪", fill="white")
    return img


class TrayManager:
    """管理系统托盘图标，实现最小化到托盘 + 播放控制"""

    def __init__(self, window, app_dir: str, window_api, docker=None):
        self._window = window
        self._app_dir = app_dir
        self._api = window_api
        self._docker = docker
        self._icon = None
        self._thread = None
        self._menu_update_timer = None
        self._last_title = ""
        self._last_is_playing = None
        self._exiting = False

    def start(self):
        """后台线程启动托盘"""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _build_menu(self):
        """构建动态托盘菜单（含播放状态和控制）"""
        import pystray

        state = self._api.get_playback_state()
        title = state.get("title", "未在播放")
        is_playing = state.get("isPlaying", False)

        # 去掉【xxx】前缀，截断至 ~12 字保持菜单紧凑
        title = re.sub(r"【[^】]*】", "", title).strip()
        display_title = title if len(title) <= 12 else title[:10] + "..."

        return pystray.Menu(
            pystray.MenuItem(display_title, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("上一首", self._on_prev),
            pystray.MenuItem("暂停" if is_playing else "播放", self._on_toggle),
            pystray.MenuItem("下一首", self._on_next),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("显示主窗口", self._on_restore, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._on_exit),
        )

    def _refresh_menu(self):
        """刷新托盘菜单（安全调用）"""
        if self._icon:
            try:
                self._icon.update_menu()
            except Exception:
                pass

    def _schedule_menu_update(self):
        """定时轮询播放状态，仅在标题或播放/暂停变化时才重建菜单"""

        def _loop():
            while self._icon is not None:
                try:
                    state = self._api.get_playback_state()
                    title = state.get("title", "未在播放")
                    is_playing = state.get("isPlaying", False)

                    # 状态未变化则跳过，避免菜单闪烁
                    if title == self._last_title and is_playing == self._last_is_playing:
                        time.sleep(2)
                        continue

                    self._last_title = title
                    self._last_is_playing = is_playing
                    self._icon._menu = self._build_menu()
                    self._icon.update_menu()
                except Exception:
                    break
                time.sleep(2)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        self._menu_update_timer = t

    def _run(self):
        import ctypes
        import pystray

        image = _get_tray_image(self._app_dir)
        self._icon = pystray.Icon(
            "BIU", image, "BIU Music Player",
            menu=self._build_menu(),
        )

        # 去掉菜单左侧 checkmark/icon 预留空白
        _orig_create = self._icon._create_menu

        class _MENUINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_uint),
                ("fMask", ctypes.c_uint),
                ("dwStyle", ctypes.c_uint),
                ("cyMax", ctypes.c_uint),
                ("hbrBack", ctypes.c_void_p),
                ("dwContextHelpID", ctypes.c_uint),
                ("dwMenuData", ctypes.c_ulong),
            ]

        def _patched_create(descriptor, callbacks):
            hmenu = _orig_create(descriptor, callbacks)
            if hmenu:
                try:
                    info = _MENUINFO()
                    info.cbSize = ctypes.sizeof(_MENUINFO)
                    info.fMask = 0x00000010        # MIM_STYLE
                    info.dwStyle = 0x04000000       # MNS_CHECKORBMP
                    ctypes.windll.user32.SetMenuInfoW(hmenu, ctypes.byref(info))
                except Exception:
                    pass
            return hmenu

        self._icon._create_menu = _patched_create

        # 启动菜单定时刷新
        self._schedule_menu_update()
        self._icon.run()

    def minimize_to_tray(self):
        """隐藏窗口到托盘"""
        try:
            self._window.hide()
        except Exception:
            pass

    def _on_restore(self):
        """从托盘恢复窗口"""
        if self._docker:
            self._docker.force_show()
        try:
            self._window.show()
        except Exception:
            pass

    def _on_toggle(self):
        """托盘：播放/暂停"""
        self._api.toggle_play()

    def _on_next(self):
        """托盘：下一首"""
        self._api.next_song()

    def _on_prev(self):
        """托盘：上一首"""
        self._api.prev_song()

    def _on_exit(self):
        """完全退出应用"""
        self._exiting = True
        if self._icon:
            self._icon.stop()
        # 不阻塞 pystray 回调线程，让图标立即消失；窗口销毁放后台
        threading.Thread(target=self._do_exit, daemon=True).start()

    def _do_exit(self):
        try:
            self._window.destroy()
        except Exception:
            pass
        os._exit(0)


# ---- 窗口吸附：拖到屏幕顶部自动隐藏，鼠标悬浮边缘显示 ----


class WindowDockManager:
    """QQ 式窗口吸附：推到屏幕顶部自动缩进，鼠标靠边滑出"""

    _DOCK_THRESHOLD = 5       # y ≤ 此值触发吸附
    _SHOW_THRESHOLD = 60      # 鼠标 y ≤ 此值触发展示
    _REHIDE_DELAY = 0.6       # 鼠标离开窗口区域后缩回等待（秒）
    _VISIBLE_STRIP = 2        # 隐藏后保留若干 px 可见
    _SLIDE_STEPS = 8          # 滑动动画帧数

    def __init__(self, window):
        self._window = window
        self._docked = False
        self._animating = False
        self._dock_x = 0
        self._dock_w = 0
        self._dock_h = 0
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

    # ---- 工具 ----
    def _geo(self):
        try:
            return self._window.x, self._window.y, self._window.width, self._window.height
        except Exception:
            return None

    def _cursor(self):
        import ctypes
        pt = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    # ---- 动画 ----
    def _slide(self, target_y: int):
        try:
            start_y = self._window.y
        except Exception:
            return
        for i in range(1, self._SLIDE_STEPS + 1):
            t = i / self._SLIDE_STEPS
            eased = t * t * (3 - 2 * t)  # ease-in-out
            try:
                self._window.move(self._dock_x, int(start_y + (target_y - start_y) * eased))
            except Exception:
                break
            time.sleep(0.01)

    def _dock(self):
        geo = self._geo()
        if not geo:
            return
        self._dock_x, _, self._dock_w, self._dock_h = geo
        self._animating = True
        self._slide(-self._dock_h + self._VISIBLE_STRIP)
        self._docked = True
        self._animating = False

    def _undock(self, target_y: int = 0):
        self._animating = True
        self._slide(target_y)
        self._docked = False
        self._animating = False

    def force_show(self):
        """强制显示（托盘恢复/外部调用）"""
        if self._docked:
            self._undock()

    # ---- 监控线程 ----
    def _monitor(self):
        time.sleep(2)  # 等窗口就绪

        while True:
            try:
                geo = self._geo()
                if not geo:
                    time.sleep(0.5)
                    continue
                x, y, w, h = geo

                # 未吸附 + 推到顶部 → 缩进
                if not self._docked and not self._animating:
                    if y <= self._DOCK_THRESHOLD and h > 0:
                        time.sleep(0.4)          # 防抖
                        geo2 = self._geo()
                        if geo2 and geo2[1] <= self._DOCK_THRESHOLD and not self._animating:
                            self._dock()

                # 已吸附 → 检测鼠标是否悬停顶部边缘
                if self._docked and not self._animating:
                    cx, cy = self._cursor()
                    if (cy <= self._SHOW_THRESHOLD and
                            self._dock_x - 20 <= cx <= self._dock_x + self._dock_w + 20):
                        self._undock()
                        # 窗口滑出后，保持展示直到鼠标离开窗口区域
                        while True:
                            time.sleep(0.3)
                            # 用户把窗口拖走了？退出吸附模式
                            geo3 = self._geo()
                            if geo3 and geo3[1] > self._DOCK_THRESHOLD:
                                break
                            cx2, cy2 = self._cursor()
                            in_win = (cy2 <= h and
                                      self._dock_x - 20 <= cx2 <= self._dock_x + self._dock_w + 20)
                            if in_win:
                                continue
                            time.sleep(self._REHIDE_DELAY)
                            cx3, cy3 = self._cursor()
                            in_win2 = (cy3 <= h and
                                       self._dock_x - 20 <= cx3 <= self._dock_x + self._dock_w + 20)
                            if not in_win2:
                                # 再次确认窗口还在顶部才缩回
                                geo4 = self._geo()
                                if geo4 and geo4[1] <= self._DOCK_THRESHOLD:
                                    self._dock()
                            break

            except Exception:
                pass
            time.sleep(0.3)


# ---- 主入口 ----
if __name__ == "__main__":
    print("=" * 50)
    print("  BIU Music Player (桌面版)")
    print("=" * 50)

    def start_flask():
        app.run(host="127.0.0.1", port=27232, debug=False)

    # 后台启动 Flask
    threading.Thread(target=start_flask, daemon=True).start()

    # 屏幕居中（ctypes 无需启动 tk 窗口，更快）
    import ctypes as _ct
    screen_w = _ct.windll.user32.GetSystemMetrics(0)
    screen_h = _ct.windll.user32.GetSystemMetrics(1)

    # 等待 Flask 就绪（轮询取代固定 sleep，更快）
    import requests as _rq
    for _ in range(20):
        time.sleep(0.05)
        try:
            _rq.get("http://127.0.0.1:27232", timeout=0.3)
            break
        except Exception:
            continue

    # 窗口控制 API
    window_api = WindowApi()

    win_w, win_h = 300, 720
    center_x = (screen_w - win_w) // 2
    center_y = (screen_h - win_h) // 2

    # 创建主窗口
    main_win = webview.create_window(
        title="BIU Music Player",
        url="http://127.0.0.1:27232",
        width=win_w,
        height=win_h,
        x=center_x,
        y=center_y,
        min_size=(300, 400),
        resizable=True,
        frameless=True,
        easy_drag=False,
        js_api=window_api,
    )
    window_api.set_main(main_win)

    # 隐藏任务栏图标：窗口只出现在系统托盘
    def _hide_from_taskbar():
        import ctypes

        hwnd = ctypes.windll.user32.FindWindowW(None, "BIU Music Player")
        if not hwnd:
            for _ in range(30):
                time.sleep(0.1)
                hwnd = ctypes.windll.user32.FindWindowW(None, "BIU Music Player")
                if hwnd:
                    break
        if not hwnd:
            return

        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000
        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style = (ex_style & ~WS_EX_APPWINDOW) | WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
        # SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE → 刷新样式
        ctypes.windll.user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0001 | 0x0002
        )

    main_win.events.shown += _hide_from_taskbar

    # 窗口吸附：推到屏幕顶部自动缩进，鼠标悬浮边缘滑出
    docker = WindowDockManager(main_win)
    docker.start()

    # 启动系统托盘：最小化/关闭 → 隐藏到托盘，通过托盘菜单退出/控制播放
    tray = TrayManager(main_win, _get_app_dir(), window_api, docker)
    tray.start()
    window_api.set_on_minimize_to_tray(tray.minimize_to_tray)

    # 拦截窗口关闭事件：关闭窗口 → 隐藏到托盘，不退出程序
    def _on_closing():
        if tray._exiting:
            return True  # 真正退出，允许销毁
        tray.minimize_to_tray()
        return False  # 阻止窗口销毁，隐藏到托盘

    main_win.events.closing += _on_closing

    webview.start(gui="edgechromium", debug=False)
