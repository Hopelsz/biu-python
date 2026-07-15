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

    if getattr(sys, "frozen", False):
        ico_path = os.path.join(sys._MEIPASS, "BIU.ico")
    else:
        ico_path = os.path.join(app_dir, "BIU.ico")

    if os.path.exists(ico_path):
        try:
            img = Image.open(ico_path)
            img = img.convert("RGBA")
            img = img.resize((32, 32), Image.LANCZOS)
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
    """管理系统托盘图标，实现关闭到托盘 + 播放控制"""

    def __init__(self, window, app_dir: str, window_api):
        self._window = window
        self._app_dir = app_dir
        self._api = window_api
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

    def _schedule_menu_update(self):
        """定时轮询播放状态变化并刷新菜单"""

        def _loop():
            while self._icon is not None:
                try:
                    state = self._api.get_playback_state()
                    title = state.get("title", "未在播放")
                    is_playing = state.get("isPlaying", False)

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
        try:
            self._window.show()
        except Exception:
            pass

    def _on_toggle(self):
        self._api.toggle_play()

    def _on_next(self):
        self._api.next_song()

    def _on_prev(self):
        self._api.prev_song()

    def _on_exit(self):
        """完全退出应用"""
        self._exiting = True
        if self._icon:
            self._icon.stop()
        threading.Thread(target=self._do_exit, daemon=True).start()

    def _do_exit(self):
        try:
            self._window.destroy()
        except Exception:
            pass
        os._exit(0)


# ---- WebView2 运行时检测 & 自动安装 ----
def _ensure_webview2():
    """检测 Edge WebView2 Runtime 是否安装，未安装则自动下载安装。"""
    import subprocess, tempfile, urllib.request

    webview2_key = r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    try:
        import winreg
        winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, webview2_key)
        return
    except OSError:
        pass

    print("[BIU] 未检测到 WebView2 运行时，正在自动安装...")
    print("[BIU] 安装大约需要 1-2 分钟，请稍候...")

    installer_path = os.path.join(tempfile.gettempdir(), "WebView2Setup.exe")
    try:
        urllib.request.urlretrieve(
            "https://go.microsoft.com/fwlink/p/?LinkId=2124703",
            installer_path
        )
        subprocess.run([installer_path, "/install"], check=True, capture_output=True)
        os.remove(installer_path)
        print("[BIU] WebView2 运行时安装完成！")
    except Exception as e:
        print(f"[BIU] 自动安装失败: {e}")
        print("[BIU] 请手动下载安装: https://developer.microsoft.com/microsoft-edge/webview2/")
        try:
            os.remove(installer_path)
        except Exception:
            pass


# ---- 主入口 ----
if __name__ == "__main__":
    import socket
    import ctypes as _ct

    # ---- 确保 WebView2 运行时可用 ----
    if sys.platform == "win32":
        _ensure_webview2()

    # ---- 允许 Ctrl+C 退出 ----
    if sys.platform == "win32":
        _ct.windll.kernel32.SetConsoleTitleW("BIU Music Player")
        _handler_type = _ct.WINFUNCTYPE(_ct.c_bool, _ct.c_ulong)

        @_handler_type
        def _console_handler(ctrl_type):
            if ctrl_type in (0, 2):
                print("\n正在退出 BIU...")
                os._exit(0)
            return False

        _ct.windll.kernel32.SetConsoleCtrlHandler(_console_handler, True)

    print("=" * 50)
    print("  BIU Music Player (桌面版)")
    print("=" * 50)

    # ---- Flask 启动 ----
    flask_ready = threading.Event()
    flask_error_msg = None

    def start_flask():
        global flask_error_msg
        try:
            from werkzeug.serving import make_server
            server = make_server("127.0.0.1", 27232, app, threaded=True)
            server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            flask_ready.set()
            server.serve_forever()
        except OSError as e:
            flask_error_msg = str(e)
            flask_ready.set()

    threading.Thread(target=start_flask, daemon=True).start()

    if not flask_ready.wait(timeout=5):
        print("错误: Flask 启动超时，请检查环境")
        os._exit(1)

    if flask_error_msg:
        print(f"错误: Flask 启动失败 - {flask_error_msg}")
        print("端口 27232 可能被占用。请在任务管理器中结束残留的 Python 进程后重试。")
        os._exit(1)

    import requests as _rq
    for _ in range(20):
        time.sleep(0.1)
        try:
            _rq.get("http://127.0.0.1:27232", timeout=0.5)
            break
        except Exception:
            continue
    else:
        print("错误: 无法连接到 Flask 服务，请检查端口 27232 是否被占用")
        os._exit(1)

    # 屏幕居中
    screen_w = _ct.windll.user32.GetSystemMetrics(0)
    screen_h = _ct.windll.user32.GetSystemMetrics(1)

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

    # 启动系统托盘
    tray = TrayManager(main_win, _get_app_dir(), window_api)
    tray.start()
    window_api.set_on_minimize_to_tray(tray.minimize_to_tray)

    # 关闭窗口 → 隐藏到托盘，任务栏图标消失，托盘图标保留
    def _on_closing():
        if tray._exiting:
            return True
        tray.minimize_to_tray()
        return False

    main_win.events.closing += _on_closing

    webview.start(gui="edgechromium", debug=False)
