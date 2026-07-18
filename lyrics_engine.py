"""
BIU - 歌词引擎
多渠道歌词搜索、缓存、B站字幕提取
"""

import concurrent.futures
import hashlib
import json
import logging
import os
import re
import threading
import urllib.parse

import requests

logger = logging.getLogger(__name__)

# 歌词缓存目录
_lyrics_cache_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".lyrics_cache"
)
os.makedirs(_lyrics_cache_dir, exist_ok=True)


# ---- 缓存读写 ----
def _lyrics_cache_path(key: str) -> str:
    safe = hashlib.md5(key.encode()).hexdigest() + ".json"
    return os.path.join(_lyrics_cache_dir, safe)


def read_lyrics_cache(key: str) -> dict | None:
    """从本地缓存读取歌词数据"""
    try:
        path = _lyrics_cache_path(key)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("lrc"):
                logger.info("lyrics: cache hit for key=%s", key)
                return data
    except Exception:
        pass
    return None


def write_lyrics_cache(key: str, data: dict):
    """写入歌词缓存到本地"""
    try:
        path = _lyrics_cache_path(key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        logger.info("lyrics: cache write for key=%s", key)
    except Exception as e:
        logger.error("lyrics: cache write error: %s", e)


# ---- 关键词清洗 ----
def clean_keyword(raw_title: str) -> str:
    """BBPlayer 风格的关键词提取：
    1. 优先提取《...》或「...」内的内容
    2. 否则去掉【...】和 "..." 装饰符号
    """
    priority = re.search(r"《(.+?)》|「(.+?)」", raw_title)
    if priority:
        kw = priority.group(1) or priority.group(2)
        logger.debug("lyrics: cleanKeyword priority match: %s", kw)
        return kw.strip()

    cleaned = re.sub(r"【[^】]*】", "", raw_title)
    cleaned = re.sub(r'"[^"]*"', "", cleaned)
    cleaned = re.sub(r'"[^"]*"', "", cleaned)
    cleaned = cleaned.strip()

    if cleaned:
        logger.debug("lyrics: cleanKeyword cleaned: %s", cleaned)
        return cleaned
    logger.debug("lyrics: cleanKeyword fallback to raw: %s", raw_title)
    return raw_title.strip()


# ---- B站 bgm_info 获取 ----
def get_bilibili_bgm_name(video_bvid: str, session, video_cid: str = "") -> str | None:
    """从 B站 /x/player/v2 接口获取视频的背景音乐真实名称"""
    if not video_bvid:
        return None
    try:
        params = {"bvid": video_bvid}
        if video_cid:
            params["cid"] = int(video_cid)
        resp = session.get(
            "https://api.bilibili.com/x/player/v2",
            params=params,
            timeout=5,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("code") != 0:
            return None
        bgm_info = data.get("data", {}).get("bgm_info")
        if not bgm_info:
            return None
        music_title = bgm_info.get("music_title", "")
        if not music_title:
            return None
        match = re.search(r"《(.+?)》", music_title)
        if match:
            logger.info("lyrics: bilibili bgm_info hit: '%s' (raw: '%s')", match.group(1), music_title)
            return match.group(1).strip()
        logger.info("lyrics: bilibili bgm_info hit: '%s'", music_title)
        return music_title.strip()
    except Exception as e:
        logger.error("lyrics: bilibili bgm_info error: %s", e)
    return None


# ---- B站字幕提取 ----
def try_bilibili_subtitle(video_bvid: str, session) -> str | None:
    """尝试从 B站获取 AI 字幕作为歌词（多数视频没有字幕）"""
    if not video_bvid:
        return None
    try:
        resp = session.get(
            "https://api.bilibili.com/x/player/v2",
            params={"bvid": video_bvid},
            timeout=4,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("code") != 0:
            return None
        subtitles = data.get("data", {}).get("subtitle", {}).get("subtitles", [])
        if not subtitles:
            return None
        sub_info = None
        for lang_hint in ("zh", "ja", "jp"):
            for s in subtitles:
                if lang_hint in (s.get("lan", "").lower()):
                    sub_info = s
                    break
            if sub_info:
                break
        if not sub_info:
            sub_info = subtitles[0]
        sub_url = sub_info.get("subtitle_url", "")
        if not sub_url:
            return None
        if sub_url.startswith("//"):
            sub_url = "https:" + sub_url
        resp2 = session.get(sub_url, timeout=4)
        if resp2.status_code != 200:
            return None
        sub_data = resp2.json()
        body = sub_data.get("body", [])
        if not body:
            return None
        lrc_lines = []
        for seg in body:
            ts = seg.get("from", 0)
            text = seg.get("content", "").strip()
            if text:
                m = int(ts // 60)
                s = ts % 60
                lrc_lines.append(f"[{m:02d}:{s:05.2f}]{text}")
        if lrc_lines:
            logger.info("lyrics: bilibili subtitle hit (%d lines)", len(lrc_lines))
            return "\n".join(lrc_lines)
    except Exception as e:
        logger.error("lyrics: bilibili subtitle error: %s", e)
    return None


# ---- 单源搜索 ----
def _search_163music(keyword: str, target_dur: float = 0) -> dict | None:
    """网易云音乐：搜索 - 时长匹配 - 歌词"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://music.163.com/",
    }
    try:
        q = urllib.parse.quote(keyword)
        resp = requests.get(
            f"http://music.163.com/api/cloudsearch/pc?s={q}&type=1&limit=10&offset=0",
            timeout=5, headers=headers
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        songs = data.get("result", {}).get("songs", [])
        if not songs:
            return None

        best = songs[0]
        if target_dur > 0:
            for s in songs[:5]:
                song_dur = s.get("dt", 0) / 1000.0
                if abs(song_dur - target_dur) <= 3:
                    best = s
                    logger.debug("lyrics: 163music duration match %ss ~ target %ss", song_dur, target_dur)
                    break

        song_id = best["id"]
        song_name = best.get("name", "?")
        ar_name = (best.get("ar") or [{}])[0].get("name", "?")
        logger.info("lyrics: 163music hit id=%s name=%s artist=%s keyword='%s'", song_id, song_name, ar_name, keyword)
    except Exception as e:
        logger.error("lyrics: 163music search error: %s", e)
        return None

    try:
        resp = requests.get(
            f"http://music.163.com/api/song/lyric?id={song_id}&lv=1&kv=1&tv=-1&rv=-1",
            timeout=5, headers=headers
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        lrc = (data.get("lrc") or {}).get("lyric", "")
        tlyric = (data.get("tlyric") or {}).get("lyric", "")
        romalrc = (data.get("romalrc") or {}).get("lyric", "")
        if lrc:
            logger.info("lyrics: 163music lyric (%d chars), tlyric=%s", len(lrc), bool(tlyric))
            return {"lrc": lrc, "tlyric": tlyric, "romalrc": romalrc}
    except Exception as e:
        logger.error("lyrics: 163music lyric error: %s", e)
    return None


def _search_qqmusic(keyword: str, target_dur: float = 0) -> dict | None:
    """QQ音乐：搜索 - 时长匹配 - 歌词（参考 BBPlayer QQMusicApi）"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://y.qq.com/",
    }
    try:
        q = urllib.parse.quote(keyword)
        resp = requests.get(
            f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={q}&n=10&format=json&t=0",
            timeout=5, headers=headers
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        songlist = data.get("data", {}).get("song", {}).get("list", [])
        if not songlist:
            return None

        best = songlist[0]
        if target_dur > 0:
            for s in songlist[:5]:
                song_dur = s.get("interval", 0)
                if abs(song_dur - target_dur) <= 3:
                    best = s
                    logger.debug("lyrics: qqmusic duration match %ss ~ target %ss", song_dur, target_dur)
                    break

        songmid = best.get("songmid", "")
        song_name = best.get("songname", "?")
        singer_name = (best.get("singer") or [{}])[0].get("name", "?")
        if not songmid:
            return None
        logger.info("lyrics: qqmusic hit mid=%s name=%s singer=%s keyword='%s'", songmid, song_name, singer_name, keyword)
    except Exception as e:
        logger.error("lyrics: qqmusic search error: %s", e)
        return None

    try:
        resp = requests.get(
            f"https://i.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
            f"?songmid={songmid}&g_tk=5381&format=json&nobase64=1",
            timeout=5, headers=headers
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("code") != 0:
            return None
        lrc = data.get("lyric", "") or data.get("lrc", "")
        trans = data.get("trans", "")
        lrc = lrc.replace("&#10;", "\n").replace("&#13;", "").replace("&#58;", ":").replace("&#46;", ".").replace("&#32;", " ")
        trans = trans.replace("&#10;", "\n").replace("&#13;", "")
        if lrc:
            logger.info("lyrics: qqmusic lyric (%d chars)", len(lrc))
            return {"lrc": lrc, "tlyric": trans, "romalrc": ""}
    except Exception as e:
        logger.error("lyrics: qqmusic lyric error: %s", e)
    return None


def _search_lrclib(keyword: str, target_dur: float = 0) -> dict | None:
    """lrclib.net 歌词搜索"""
    headers = {"User-Agent": "BIU Music Player/1.0"}
    try:
        resp = requests.get("https://lrclib.net/api/search",
                            params={"q": keyword}, timeout=3, headers=headers)
        if resp.status_code != 200:
            return None
        results = resp.json()
        if not results:
            return None

        best = results[0]
        if target_dur > 0:
            for r in results[:5]:
                rd = r.get("duration") or 0
                if rd > 0 and abs(rd - target_dur) <= 3:
                    best = r
                    break

        lrc = best.get("syncedLyrics") or best.get("plainLyrics")
        if lrc:
            logger.info("lyrics: lrclib hit track=%s artist=%s",
                        best.get("trackName", "?"), best.get("artistName", "?"))
            return {"lrc": lrc, "tlyric": "", "romalrc": ""}
    except Exception:
        pass
    return None


# ---- 多源并行搜索 ----
def search_lyrics_multisource(keyword: str, duration_sec: float = 0) -> dict | None:
    """多源并行搜索歌词，采用竞速模式，返回第一个有效结果"""
    done_event = threading.Event()
    result_lock = threading.Lock()
    shared_result = [None]

    def _runner(func, kw, dur):
        if done_event.is_set():
            return
        try:
            r = func(kw, dur)
        except Exception:
            r = None
        if r and not done_event.is_set():
            with result_lock:
                if not done_event.is_set():
                    done_event.set()
                    shared_result[0] = r

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        futures.append(executor.submit(_runner, _search_163music, keyword, duration_sec))
        futures.append(executor.submit(_runner, _search_qqmusic, keyword, duration_sec))
        futures.append(executor.submit(_runner, _search_lrclib, keyword, duration_sec))

        concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
        if shared_result[0] is None:
            concurrent.futures.wait(futures)

    return shared_result[0]


# ---- 搜索候选列表（用于手动搜索） ----
def search_lyrics_candidates(keyword: str, duration_sec: float = 0) -> list:
    """多源搜索歌词候选列表，按时长匹配排序"""
    headers_163 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://music.163.com/",
    }
    headers_qq = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://y.qq.com/",
    }
    headers_lrc = {"User-Agent": "BIU Music Player/1.0"}

    def _s_163(kw):
        try:
            q = urllib.parse.quote(kw)
            resp = requests.get(
                f"http://music.163.com/api/cloudsearch/pc?s={q}&type=1&limit=6&offset=0",
                timeout=5, headers=headers_163
            )
            if resp.status_code != 200:
                return []
            songs = resp.json().get("result", {}).get("songs", [])
            return [
                {"source": "netease", "id": str(s["id"]),
                 "title": s.get("name", "?"),
                 "artist": (s.get("ar") or [{}])[0].get("name", "?"),
                 "duration": int((s.get("dt") or 0) / 1000.0)}
                for s in songs[:6]
            ]
        except Exception:
            return []

    def _s_qq(kw):
        try:
            q = urllib.parse.quote(kw)
            resp = requests.get(
                f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={q}&n=6&format=json&t=0",
                timeout=5, headers=headers_qq
            )
            if resp.status_code != 200:
                return []
            songlist = resp.json().get("data", {}).get("song", {}).get("list", [])
            return [
                {"source": "qqmusic", "id": s.get("songmid", ""),
                 "title": s.get("songname", "?"),
                 "artist": (s.get("singer") or [{}])[0].get("name", "?"),
                 "duration": s.get("interval", 0)}
                for s in songlist[:6]
            ]
        except Exception:
            return []

    def _s_lrclib(kw):
        try:
            resp = requests.get("https://lrclib.net/api/search",
                                params={"q": kw}, timeout=3, headers=headers_lrc)
            if resp.status_code != 200:
                return []
            items = resp.json()
            return [
                {"source": "lrclib", "id": str(r.get("id", "")),
                 "title": r.get("trackName", "?"),
                 "artist": r.get("artistName", "?"),
                 "duration": r.get("duration") or 0}
                for r in items[:6]
            ]
        except Exception:
            return []

    search_results = {"netease": [], "qqmusic": [], "lrclib": []}

    def _runner(src, fn):
        search_results[src] = fn(keyword)

    threads = [
        threading.Thread(target=_runner, args=("netease", _s_163)),
        threading.Thread(target=_runner, args=("qqmusic", _s_qq)),
        threading.Thread(target=_runner, args=("lrclib", _s_lrclib)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=6)

    all_results = search_results["netease"] + search_results["qqmusic"] + search_results["lrclib"]

    if duration_sec > 0:
        def _sort_key(r):
            d = r.get("duration", 0)
            return abs(d - duration_sec) if d > 0 else 999
        all_results.sort(key=_sort_key)

    return all_results


# ---- 根据源和ID获取歌词 ----
def fetch_lyrics_by_source(source: str, song_id: str) -> dict:
    """根据歌词源和歌曲 ID 获取完整歌词（含翻译/罗马音）"""
    headers_163 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://music.163.com/",
    }
    headers_qq = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://y.qq.com/",
    }

    result = {}
    if source == "netease":
        try:
            resp = requests.get(
                f"http://music.163.com/api/song/lyric?id={song_id}&lv=1&kv=1&tv=-1&rv=-1",
                timeout=5, headers=headers_163
            )
            if resp.status_code == 200:
                data = resp.json()
                result["lrc"] = (data.get("lrc") or {}).get("lyric", "")
                result["tlyric"] = (data.get("tlyric") or {}).get("lyric", "")
                result["romalrc"] = (data.get("romalrc") or {}).get("lyric", "")
        except Exception as e:
            logger.error("lyrics: fetch netease error: %s", e)

    elif source == "qqmusic":
        try:
            resp = requests.get(
                f"https://i.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
                f"?songmid={song_id}&g_tk=5381&format=json&nobase64=1",
                timeout=5, headers=headers_qq
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    lrc = data.get("lyric", "") or data.get("lrc", "")
                    lrc = lrc.replace("&#10;", "\n").replace("&#13;", "").replace("&#58;", ":").replace("&#46;", ".").replace("&#32;", " ")
                    trans = data.get("trans", "")
                    trans = trans.replace("&#10;", "\n").replace("&#13;", "")
                    result["lrc"] = lrc
                    result["tlyric"] = trans
                    result["romalrc"] = ""
        except Exception as e:
            logger.error("lyrics: fetch qqmusic error: %s", e)

    elif source == "lrclib":
        try:
            headers_lrc = {"User-Agent": "BIU Music Player/1.0"}
            resp = requests.get(f"https://lrclib.net/api/get/{song_id}",
                                timeout=3, headers=headers_lrc)
            if resp.status_code == 200:
                data = resp.json()
                lrc = data.get("syncedLyrics") or data.get("plainLyrics") or ""
                result["lrc"] = lrc
                result["tlyric"] = ""
                result["romalrc"] = ""
        except Exception as e:
            logger.error("lyrics: fetch lrclib error: %s", e)

    if result.get("lrc"):
        result["ok"] = True
    else:
        result = {"ok": False}
    return result
