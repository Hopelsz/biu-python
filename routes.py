"""
BIU - Flask API 路由 & 窗口控制
"""
import json
import logging
import time

import requests
from flask import Response, jsonify, request

import lyrics_engine

logger = logging.getLogger(__name__)

# 记录曾经成功响应的 CDN 主机，下次优先使用
_GOOD_CDN_HOSTS: set[str] = set()

# ---- API 频率限制 ----
_LAST_CALL: dict[str, float] = {}

def _rate_limit(key: str, min_interval: float = 0.3) -> bool:
    """简单的 API 频率限制，返回 True 表示允许调用"""
    now = time.time()
    if key in _LAST_CALL and now - _LAST_CALL[key] < min_interval:
        return False
    _LAST_CALL[key] = now
    return True


def _extract_host(url: str) -> str:
    """从 URL 中提取 host:port"""
    return url.split("/")[2] if "://" in url and url.count("/") >= 3 else ""


class WindowApi:
    """主窗口 JS API —— 窗口控制 + 播放控制"""

    def __init__(self):
        self._main_window = None
        self._on_minimize_to_tray = None

    def set_main(self, w):
        self._main_window = w

    def set_on_minimize_to_tray(self, callback):
        """设置最小化到托盘的钩子；设置后 minimize/close 都会走托盘"""
        self._on_minimize_to_tray = callback

    def restore(self):
        """恢复主窗口（从托盘或被其他实例唤醒）"""
        if self._main_window:
            try:
                self._main_window.show()
            except Exception:
                pass

    def minimize(self):
        """正常最小化到任务栏"""
        if self._main_window:
            self._main_window.minimize()

    def move_window(self, x, y):
        x, y = int(x), int(y)
        if self._main_window:
            self._main_window.move(x, y)

    def close(self):
        if self._on_minimize_to_tray:
            self._on_minimize_to_tray()
        elif self._main_window:
            self._main_window.destroy()

    # ---- 播放控制（供托盘菜单调用）----
    def _eval(self, js: str):
        """在 webview 中执行 JS，忽略异常"""
        if self._main_window:
            try:
                self._main_window.evaluate_js(js)
            except Exception:
                pass

    def toggle_play(self):
        self._eval("togglePlay()")

    def next_song(self):
        self._eval("nextSong()")

    def prev_song(self):
        self._eval("prevSong()")

    def get_playback_state(self) -> dict:
        """获取前端播放状态，供托盘轮询"""
        if self._main_window:
            try:
                raw = self._main_window.evaluate_js("getPlaybackState()")
                if raw and isinstance(raw, str):
                    return json.loads(raw)
            except Exception:
                pass
        return {"title": "未在播放", "isPlaying": False}


def register_routes(app, client, load_config, save_config, window_api=None):
    """向 Flask app 注册所有 API 路由"""
    _api = window_api

    # ---- 主页 ----
    @app.route("/")
    def index():
        from flask import render_template
        return render_template("index.html")

    # ---- 单实例：第二实例唤醒主窗口 ----
    @app.route("/api/restore", methods=["POST"])
    def api_restore():
        if _api:
            _api.restore()
        return jsonify({"ok": True})

    # ---- 登录 / 登出 ----
    @app.route("/api/login", methods=["POST"])
    def api_login():
        data = request.get_json()
        sessdata = data.get("sessdata", "").strip()
        if not sessdata:
            return jsonify({"ok": False, "error": "请输入 SESSDATA"})

        client.set_cookie(sessdata)
        try:
            mid = client.get_self_mid()
        except Exception as e:
            logger.error("login exception: %s", e)
            return jsonify({"ok": False, "error": "请求失败，请检查网络连接"})

        if not mid:
            return jsonify({"ok": False, "error": "SESSDATA 无效或已过期，请重新获取"})

        cfg = load_config()
        cfg["sessdata"] = sessdata
        cfg["buvid"] = client._buvid
        save_config(cfg)
        return jsonify({"ok": True, "mid": mid})

    @app.route("/api/logout", methods=["POST"])
    def api_logout():
        cfg = load_config()
        cfg.pop("sessdata", None)
        cfg.pop("buvid", None)
        save_config(cfg)
        client.set_cookie("")
        client._buvid = None
        return jsonify({"ok": True})

    # ---- 用户信息 ----
    @app.route("/api/user")
    def api_user():
        mid = client.get_self_mid()
        if mid:
            return jsonify({
                "logged_in": True,
                "mid": mid,
                "uname": client._uname,
                "face": client._face,
            })
        return jsonify({"logged_in": False})

    # ---- 收藏夹列表 ----
    @app.route("/api/folders")
    def api_folders():
        try:
            folders = client.get_fav_folders()
            logger.info("API /api/folders: returning %s folders", len(folders))
            return jsonify(folders)
        except Exception as e:
            logger.error("API /api/folders error: %s", e)
            return jsonify([])

    # ---- 收藏夹信息（含封面） ----
    @app.route("/api/folder-info")
    def api_folder_info():
        media_id = request.args.get("media_id", type=int)
        if not media_id:
            return jsonify(None)
        try:
            info = client.get_fav_folder_info(media_id)
            return jsonify(info)
        except Exception as e:
            logger.error("API /api/folder-info error: %s", e)
            return jsonify(None)

    # ---- 隐藏收藏夹配置 ----
    @app.route("/api/hidden-folders", methods=["GET", "POST"])
    def api_hidden_folders():
        cfg = load_config()
        if request.method == "GET":
            return jsonify({"hidden": cfg.get("hidden_folders", [])})
        else:
            data = request.get_json() or {}
            cfg["hidden_folders"] = data.get("hidden", [])
            save_config(cfg)
            return jsonify({"ok": True})

    # ---- 系统设置 ----
    @app.route("/api/system-settings", methods=["GET", "POST"])
    def api_system_settings():
        cfg = load_config()
        sys_cfg = cfg.get("system", {})
        if request.method == "GET":
            return jsonify({
                "font_family": sys_cfg.get("font_family", "default"),
                "theme": sys_cfg.get("theme", "dark"),
                "display_remark": sys_cfg.get("display_remark", False),
                "show_up": sys_cfg.get("show_up", True),
                "show_duration": sys_cfg.get("show_duration", True),
            })
        else:
            data = request.get_json() or {}
            cfg["system"] = {
                "font_family": data.get("font_family", sys_cfg.get("font_family", "default")),
                "theme": data.get("theme", sys_cfg.get("theme", "dark")),
                "display_remark": data.get("display_remark", sys_cfg.get("display_remark", False)),
                "show_up": data.get("show_up", sys_cfg.get("show_up", True)),
                "show_duration": data.get("show_duration", sys_cfg.get("show_duration", True)),
            }
            save_config(cfg)
            return jsonify({"ok": True})

    # ---- 歌曲备注 ----
    @app.route("/api/remarks", methods=["GET", "POST"])
    def api_remarks():
        cfg = load_config()
        if request.method == "GET":
            return jsonify(cfg.get("remarks", {}))
        else:
            data = request.get_json() or {}
            bvid = data.get("bvid", "").strip()
            remark = data.get("remark", "").strip()
            if not bvid:
                return jsonify({"ok": False, "error": "缺少 bvid"})
            remarks = cfg.get("remarks", {})
            if remark:
                remarks[bvid] = remark
            elif bvid in remarks:
                del remarks[bvid]
            cfg["remarks"] = remarks
            save_config(cfg)
            return jsonify({"ok": True})

    # ---- 收藏夹内容 ----
    @app.route("/api/folder-content")
    def api_folder_content():
        media_id = request.args.get("media_id", type=int)
        page = request.args.get("page", 1, type=int)
        if not media_id:
            return jsonify({"items": [], "has_more": False, "error": "missing media_id"})
        try:
            result = client.get_fav_folder_content(media_id, page)
            return jsonify(result)
        except Exception as e:
            logger.error("API /api/folder-content error: %s", e)
            return jsonify({"items": [], "has_more": False, "error": str(e)})

    # ---- 全站搜索 ----
    @app.route("/api/search")
    def api_search():
        q = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)
        if not q:
            return jsonify({"items": [], "has_more": False, "total": 0, "page": 1})
        try:
            result = client.search_videos(q, page)
            return jsonify(result)
        except Exception as e:
            logger.error("API /api/search error: %s", e)
            return jsonify({"items": [], "has_more": False, "total": 0, "page": page})

    # ---- 歌词 (调用 lyrics_engine) ----
    @app.route("/api/lyrics")
    def api_lyrics():
        if not _rate_limit("lyrics", 0.5):
            return jsonify({"ok": False, "error": "too many requests"}), 429

        title = request.args.get("title", "").strip()
        artist = request.args.get("artist", "").strip()
        bvid = request.args.get("bvid", "").strip()
        cid = request.args.get("cid", "").strip()
        dur_str = request.args.get("duration", "0")
        duration_sec = float(dur_str) if dur_str else 0

        if not title:
            return jsonify({"ok": False, "error": "missing title"})

        # 1. 本地缓存
        cache_key = bvid or title
        if bvid and cid:
            cache_key = f"{bvid}:{cid}"
        cached = lyrics_engine.read_lyrics_cache(cache_key)
        if cached:
            resp = {"ok": True, "lrc": cached["lrc"]}
            if cached.get("tlyric"):
                resp["tlyric"] = cached["tlyric"]
            if cached.get("romalrc"):
                resp["romalrc"] = cached["romalrc"]
            return jsonify(resp)

        # 2. B站字幕（兜底）
        if bvid:
            lrc_text = lyrics_engine.try_bilibili_subtitle(bvid, client.session)
            if lrc_text:
                data = {"lrc": lrc_text, "tlyric": "", "romalrc": ""}
                lyrics_engine.write_lyrics_cache(cache_key, data)
                return jsonify({"ok": True, "lrc": lrc_text})

        # 3. 提取关键词
        keyword = None
        if bvid:
            bgm_name = lyrics_engine.get_bilibili_bgm_name(bvid, client.session, cid)
            if bgm_name:
                keyword = bgm_name
                logger.info("lyrics: using bilibili bgm_name='%s'", keyword)
        if not keyword:
            keyword = lyrics_engine.clean_keyword(title)
        logger.info("lyrics: final keyword='%s' duration=%ss", keyword, duration_sec)

        # 4. 多源并行搜索
        lrc_result = lyrics_engine.search_lyrics_multisource(keyword, duration_sec)
        if lrc_result and isinstance(lrc_result, dict) and lrc_result.get("lrc"):
            lyrics_engine.write_lyrics_cache(cache_key, lrc_result)
            resp = {"ok": True, "lrc": lrc_result["lrc"]}
            if lrc_result.get("tlyric"):
                resp["tlyric"] = lrc_result["tlyric"]
            if lrc_result.get("romalrc"):
                resp["romalrc"] = lrc_result["romalrc"]
            return jsonify(resp)

        return jsonify({"ok": False})

    @app.route("/api/lyrics/search")
    def api_lyrics_search():
        if not _rate_limit("lyrics_search", 0.5):
            return jsonify({"ok": False, "error": "too many requests"}), 429

        keyword = request.args.get("keyword", "").strip()
        dur_str = request.args.get("duration", "0")
        duration_sec = float(dur_str) if dur_str else 0

        if not keyword:
            return jsonify({"ok": False, "error": "missing keyword"})

        results = lyrics_engine.search_lyrics_candidates(keyword, duration_sec)
        return jsonify({"ok": True, "keyword": keyword, "results": results})

    @app.route("/api/lyrics/fetch")
    def api_lyrics_fetch():
        source = request.args.get("source", "").strip()
        song_id = request.args.get("id", "").strip()

        if not source or not song_id:
            return jsonify({"ok": False, "error": "missing source or id"})

        result = lyrics_engine.fetch_lyrics_by_source(source, song_id)
        return jsonify(result)

    # ---- 音频代理 ----
    @app.route("/api/audio")
    def api_audio():
        bvid = request.args.get("bvid", "")
        if not bvid:
            return Response("missing bvid", status=400)

        info = client.get_play_info(bvid)
        if not info or not info.get("audio_urls"):
            return Response("no audio url", status=404)
        audio_urls = info["audio_urls"]
        logger.info("audio proxy: bvid=%s cid=%s %s url(s)", bvid, info.get("cid"), len(audio_urls))

        # 优先尝试已知可用的 CDN 主机，并把非标准端口放到最后
        audio_urls.sort(key=lambda u: (
            _extract_host(u) not in _GOOD_CDN_HOSTS,
            ":443" not in u and ":8082" in u,
        ))

        # 遍历所有 CDN URL（主 + 备用），逐个尝试
        for url_idx, audio_url in enumerate(audio_urls):
            host = audio_url.split("/")[2] if "/" in audio_url else "?"
            logger.debug("trying CDN #%s: %s", url_idx + 1, host)
            for attempt in range(3):
                try:
                    headers = {
                        "Referer": "https://www.bilibili.com/",
                        "Origin": "https://www.bilibili.com",
                        "Accept": "*/*",
                    }
                    if attempt == 0:
                        headers["Range"] = "bytes=0-"

                    stream_resp = client.session.get(
                        audio_url,
                        headers=headers,
                        stream=True,
                        timeout=(10, 30),
                    )
                    logger.debug("audio CDN status: %s (url #%s attempt %s)", stream_resp.status_code, url_idx + 1, attempt + 1)
                    if stream_resp.status_code >= 400:
                        logger.warning("audio CDN returned %s, retrying...", stream_resp.status_code)
                        time.sleep(0.3)
                        continue
                    stream_resp.raise_for_status()

                    def generate():
                        for chunk in stream_resp.iter_content(chunk_size=8192):
                            if chunk:
                                yield chunk

                    content_type = stream_resp.headers.get("Content-Type", "audio/mp4")
                    _GOOD_CDN_HOSTS.add(host)
                    return Response(
                        generate(),
                        status=200,
                        content_type=content_type,
                        headers={
                            "Accept-Ranges": "bytes",
                            "Content-Length": stream_resp.headers.get("Content-Length", ""),
                        },
                    )
                except requests.exceptions.ConnectionError as e:
                    logger.warning("CDN #%s unreachable (attempt %s): %s", url_idx + 1, attempt + 1, e)
                    time.sleep(0.5)
                except Exception as e:
                    logger.error("CDN #%s attempt %s error: %s", url_idx + 1, attempt + 1, e)
                    time.sleep(0.5)

        logger.error("audio proxy all CDN urls exhausted")
        return Response("audio proxy error", status=502)
