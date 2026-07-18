"""
Bilibili API 客户端
- WBI 签名
- 收藏夹
- 播放地址获取
- 扫码登录
"""
import hashlib
import io
import logging
import time
import uuid
from urllib.parse import unquote

import requests

API_BASE = "https://api.bilibili.com"

# WBI 混音密钥编码表
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 52, 44, 34,
]

logger = logging.getLogger("bilibili")


def _generate_buvid3() -> str:
    """生成 buvid3（B站设备标识）"""
    uid = uuid.uuid4()
    return f"{uid.hex[8:16]}-{uid.hex[4:8]}-{uid.hex[0:4]}-{uid.hex[16:20]}-{uid.hex[20:32]}"


class BiliClient:
    """Bilibili API 客户端"""

    def __init__(self, sessdata: str = "", buvid: str = ""):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.bilibili.com/",
            "Origin": "https://www.bilibili.com",
        })
        self._sessdata = sessdata
        self._mid: int | None = None
        self._uname: str = ""
        self._face: str = ""
        self._wbi_img_key: str = ""
        self._wbi_sub_key: str = ""
        self._buvid = buvid or _generate_buvid3()

        # 设置基础 cookie
        self.session.cookies.set("buvid3", self._buvid, domain=".bilibili.com")
        self.session.cookies.set("buvid4", str(uuid.uuid4()), domain=".bilibili.com")
        self.session.cookies.set("b_nut", str(int(time.time())), domain=".bilibili.com")
        self.session.cookies.set("_uuid", (
            f"{uuid.uuid4().hex[0:8]}-{uuid.uuid4().hex[0:4]}"
            f"-{uuid.uuid4().hex[0:4]}-{uuid.uuid4().hex[0:4]}"
            f"-{uuid.uuid4().hex[0:12]}infoc"
        ), domain=".bilibili.com")

        if sessdata:
            self.set_cookie(sessdata)

    # ---- Cookie ----

    def set_cookie(self, sessdata: str):
        """设置 SESSDATA cookie"""
        # URL 解码（从浏览器复制时 SESSDATA 常被编码，如 %2C→,  %2A→*）
        decoded = unquote(sessdata)
        self._sessdata = decoded
        logger.info("SESSDATA: %s...", decoded[:12])
        self.session.cookies.set("SESSDATA", decoded, domain=".bilibili.com")
        self._mid = None  # 重置缓存，下次重新验证
        self._wbi_img_key = ""  # 重置 WBI 密钥
        self._wbi_sub_key = ""

    # ---- 用户信息 ----

    def get_self_mid(self) -> int | None:
        """获取当前登录用户的 mid"""
        if self._mid:
            return self._mid
        try:
            resp = self.session.get(
                f"{API_BASE}/x/web-interface/nav",
                timeout=10,
            )
            data = resp.json()
            logger.info("nav response: code=%s isLogin=%s", data.get("code"), data.get("data", {}).get("isLogin"))

            if data.get("code") == 0 and data["data"].get("isLogin"):
                self._mid = data["data"]["mid"]
                self._uname = data["data"].get("uname", "")
                self._face = data["data"].get("face", "")
                # 同时缓存 WBI 密钥
                wbi_img = data["data"].get("wbi_img", {})
                if wbi_img:
                    img_url = wbi_img.get("img_url", "")
                    sub_url = wbi_img.get("sub_url", "")
                    self._wbi_img_key = img_url.rsplit("/", 1)[-1].split(".")[0]
                    self._wbi_sub_key = sub_url.rsplit("/", 1)[-1].split(".")[0]
                    logger.debug("WBI keys cached: img=%s sub=%s", self._wbi_img_key[:8], self._wbi_sub_key[:8])
                return self._mid
            else:
                logger.warning("nav login failed: code=%s msg=%s", data.get("code"), data.get("message"))
        except Exception as e:
            logger.error("nav request error: %s", e)
        return None

    # ---- WBI 签名 ----

    def _get_mixin_key(self) -> str:
        """生成混音密钥"""
        raw = self._wbi_img_key + self._wbi_sub_key
        return "".join(raw[n] for n in MIXIN_KEY_ENC_TAB)[:32]

    def _sign_params(self, params: dict) -> dict:
        """对请求参数进行 WBI 签名"""
        if not self._wbi_img_key or not self._wbi_sub_key:
            return params
        mixin_key = self._get_mixin_key()
        params["wts"] = int(time.time())
        # 按 key 排序，过滤特殊字符 '!()*
        sorted_keys = sorted(k for k in params if params[k] is not None)
        filtered_chars = set("'!()*")
        query = "&".join(
            f"{k}={''.join(ch for ch in str(params[k]) if ch not in filtered_chars)}"
            for k in sorted_keys
        )
        params["w_rid"] = hashlib.md5((query + mixin_key).encode()).hexdigest()
        logger.debug("WBI signed query: %s", query[:200])
        return params

    # ---- 收藏夹 ----

    def get_fav_folders(self) -> list[dict]:
        """获取用户创建的全部收藏夹"""
        mid = self.get_self_mid()
        if not mid:
            logger.warning("get_fav_folders: not logged in")
            return []

        # 先尝试 navnum 获取总数（失败或返回0也会继续拉取兜底）
        total = 0
        try:
            resp = self.session.get(
                f"{API_BASE}/x/space/navnum",
                params={"mid": mid},
                timeout=10,
            )
            nav = resp.json()
            logger.debug("navnum raw: code=%s favourite=%s",
                        nav.get("code"),
                        nav.get("data", {}).get("favourite"))
            if nav.get("code") == 0:
                total = nav.get("data", {}).get("favourite", {}).get("master", 0)
            logger.debug("fav folder total from navnum: %s", total)
        except Exception as e:
            logger.error("navnum error: %s", e)

        # 分页获取（navnum 返回 0 时也至少拉第1页兜底）
        page_size = 50
        max_pages = max((total + page_size - 1) // page_size, 1) if total else 2
        folders = []

        for pn in range(1, max_pages + 1):
            try:
                resp = self.session.get(
                    f"{API_BASE}/x/v3/fav/folder/created/list-all",
                    params={"up_mid": mid, "ps": page_size, "pn": pn},
                    timeout=15,
                )
                if not resp.text or not resp.text.strip():
                    logger.error("folder list page %s: empty response", pn)
                    continue
                data = resp.json()
                logger.debug("folder list page %s: code=%s count=%s msg=%s",
                            pn, data.get("code"),
                            len(data.get("data", {}).get("list", [])),
                            data.get("message"))
                if data.get("code") != 0:
                    continue
                page_list = data.get("data", {}).get("list", [])
                for item in page_list:
                    folders.append({
                        "id": item["id"],
                        "title": item["title"],
                        "cover": "",
                        "count": item.get("media_count", 0),
                    })
                if len(page_list) < page_size:
                    break
                # navnum=0 时动态扩展页码范围
                if not total and pn >= max_pages - 1:
                    max_pages += 1
            except Exception as e:
                logger.error("folder list page %s error: %s", pn, e)
                continue

        logger.info("get_fav_folders returning %s folders", len(folders))
        return folders

    def get_fav_folder_info(self, media_id: int) -> dict | None:
        """获取单个收藏夹信息（含封面），返回 {id, title, cover, count}"""
        self._ensure_wbi_keys()
        try:
            params = self._sign_params({"media_id": media_id, "platform": "web"})
            resp = self.session.get(
                f"{API_BASE}/x/v3/fav/folder/info",
                params=params,
                timeout=10,
            )
            if not resp.text or not resp.text.strip():
                return None
            data = resp.json()
            if data.get("code") != 0:
                return None
            info = data.get("data", {})
            return {
                "id": info.get("id", media_id),
                "title": info.get("title", ""),
                "cover": info.get("cover", ""),
                "count": info.get("media_count", 0),
            }
        except Exception as e:
            logger.error("get_fav_folder_info error: %s", e)
            return None

    def get_fav_folder_content(self, media_id: int, page: int = 1) -> dict:
        """获取收藏夹内容列表，返回 {items, has_more, total}"""
        self._ensure_wbi_keys()
        try:
            params = self._sign_params({
                "media_id": media_id,
                "pn": page,
                "ps": 20,
                "platform": "web",
            })
            resp = self.session.get(
                f"{API_BASE}/x/v3/fav/resource/list",
                params=params,
                timeout=15,
            )
            logger.debug("fav content: status=%s media_id=%s page=%s",
                        resp.status_code, media_id, page)
            if not resp.text or not resp.text.strip():
                logger.error("fav content: empty body, status=%s", resp.status_code)
                return {"items": [], "has_more": False, "total": 0}
            data = resp.json()
            logger.debug("fav content: code=%s msg=%s",
                        data.get("code"), data.get("message"))
            if data.get("code") != 0:
                return {"items": [], "has_more": False, "total": 0}

            result = data["data"]
            items = []
            for m in result.get("medias", []):
                items.append({
                    "id": m["id"],
                    "bvid": m.get("bvid", ""),
                    "title": m["title"],
                    "cover": m.get("cover", ""),
                    "duration": m.get("duration", 0),
                    "upper_name": m.get("upper", {}).get("name", ""),
                    "type": m.get("type", 2),
                })

            logger.debug("fav content: got %s items", len(items))
            return {
                "items": items,
                "has_more": result.get("has_more", False),
                "total": result.get("info", {}).get("media_count", len(items)),
            }
        except Exception as e:
            logger.error("fav content error: %s", e)
            return {"items": [], "has_more": False, "total": 0}

    # ---- 搜索 ----

    def search_videos(self, keyword: str, page: int = 1) -> dict:
        """搜索全站视频，返回 {items, has_more, total, page}"""
        self._ensure_wbi_keys()
        params = self._sign_params({
            "search_type": "video",
            "keyword": keyword,
            "page": page,
            "page_size": 20,
        })
        try:
            resp = self.session.get(
                f"{API_BASE}/x/web-interface/wbi/search/type",
                params=params,
                timeout=10,
            )
            data = resp.json()
            logger.debug("search: code=%s keyword=%s page=%s", data.get("code"), keyword, page)
            if data.get("code") != 0:
                return {"items": [], "has_more": False, "total": 0, "page": page}

            result = data.get("data", {})
            items = []
            for v in result.get("result") or []:
                # 解析时长字符串（如 "3:45"）→ 秒数
                dur_str = v.get("duration", "0:00")
                dur_parts = dur_str.split(":")
                dur_sec = int(dur_parts[0]) * 60 + int(dur_parts[1]) if len(dur_parts) == 2 else 0

                items.append({
                    "bvid": v.get("bvid", ""),
                    "title": v.get("title", "").replace('<em class="keyword">', '').replace('</em>', ''),
                    "author": v.get("author", ""),
                    "duration": dur_str,
                    "duration_sec": dur_sec,
                    "cover": v.get("pic", ""),
                    "play": v.get("play", 0),
                })

            total = result.get("numResults", 0)
            num_pages = result.get("numPages", 0)
            has_more = page < num_pages
            logger.info("search: found %s items, total=%s, has_more=%s", len(items), total, has_more)
            return {"items": items, "has_more": has_more, "total": total, "page": page}
        except Exception as e:
            logger.error("search error: %s", e)
            return {"items": [], "has_more": False, "total": 0, "page": page}

    # ---- 播放地址 ----

    def get_video_cid(self, bvid: str) -> int | None:
        """获取视频的第一个 cid"""
        try:
            resp = self.session.get(
                f"{API_BASE}/x/web-interface/view",
                params={"bvid": bvid},
            )
            data = resp.json()
            logger.debug("video view: bvid=%s code=%s", bvid, data.get("code"))
            if data.get("code") == 0:
                cid = data["data"].get("cid") or (
                    data["data"]["pages"][0]["cid"]
                    if data["data"].get("pages")
                    else None
                )
                logger.debug("got cid=%s for bvid=%s", cid, bvid)
                return cid
            else:
                logger.warning("video view failed: %s", data.get("message"))
        except Exception as e:
            logger.error("video view error: %s", e)
        return None

    def _ensure_wbi_keys(self):
        """确保 WBI 密钥已缓存，如果没有则先调 nav 获取"""
        if not self._wbi_img_key or not self._wbi_sub_key:
            logger.info("WBI keys not cached, fetching from nav...")
            self._mid = None
            self.get_self_mid()

    def get_audio_urls(self, bvid: str, cid: int) -> list[str] | None:
        """获取 DASH 音频流地址列表（主 URL + 备用 URL），用于 CDN 容错切换"""
        self._ensure_wbi_keys()

        params = self._sign_params({
            "bvid": bvid,
            "cid": cid,
            "fnval": 16,
            "fnver": 0,
            "platform": "web",
        })
        logger.debug("playurl params: w_rid=%s wts=%s", params.get("w_rid", "N/A"), params.get("wts", "N/A"))

        def _collect_urls(item: dict) -> list[str]:
            """从单个音频 item 中收集所有 URL（主 + 备用）"""
            urls = []
            primary = item.get("base_url") or item.get("baseUrl") or item.get("url")
            if primary:
                urls.append(primary)
            backups = item.get("backup_url") or item.get("backupUrl") or []
            if isinstance(backups, list):
                for u in backups:
                    if u and u not in urls:
                        urls.append(u)
            return urls

        try:
            resp = self.session.get(
                f"{API_BASE}/x/player/wbi/playurl",
                params=params,
                timeout=10,
            )
            data = resp.json()
            logger.debug("playurl response for %s: code=%s", bvid, data.get("code"))
            if data.get("code") != 0:
                logger.warning("playurl failed: code=%s msg=%s", data.get("code"), data.get("message"))
                return None

            result = data.get("data", {})
            dash = result.get("dash", {})
            urls = None

            # 优先选无损 FLAC
            flac = result.get("flac")
            if flac and flac.get("audio"):
                urls = _collect_urls(flac["audio"])
                if urls:
                    logger.debug("using FLAC audio, %s url(s)", len(urls))

            # DASH 音频
            if not urls:
                audios = dash.get("audio", [])
                if audios:
                    best = max(audios, key=lambda a: a.get("bandwidth", 0))
                    urls = _collect_urls(best)
                    logger.debug("using DASH audio: codec=%s bandwidth=%s %s url(s)",
                                best.get("codecs", "?"), best.get("bandwidth", 0), len(urls))

            # 兜底：非 DASH 的 durl 格式
            if not urls:
                durl = result.get("durl")
                if durl and isinstance(durl, list) and len(durl) > 0:
                    urls = _collect_urls(durl[0])
                    logger.debug("using durl audio, %s url(s)", len(urls))

            if not urls:
                logger.warning("no audio streams found in playurl response")
                return None
            return urls
        except Exception as e:
            logger.error("playurl error: %s", e)
            return None

    def get_play_info(self, bvid: str) -> dict | None:
        """一站式获取播放信息：cid + audio_url"""
        cid = self.get_video_cid(bvid)
        if not cid:
            logger.warning("get_play_info: no cid for bvid=%s", bvid)
            return None
        audio_urls = self.get_audio_urls(bvid, cid)
        if not audio_urls:
            logger.warning("get_play_info: no audio_urls for bvid=%s cid=%s", bvid, cid)
            return None
        logger.debug("get_play_info success: bvid=%s, %s url(s)", bvid, len(audio_urls))
        return {"bvid": bvid, "cid": cid, "audio_urls": audio_urls}

    # ---- 扫码登录 ----

    def get_qrcode(self) -> dict | None:
        """获取登录二维码 URL 和 qrcode_key"""
        try:
            resp = self.session.get(
                "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
                timeout=10,
            )
            data = resp.json()
            logger.info("qrcode generate: code=%s", data.get("code"))
            if data.get("code") == 0:
                qr_data = data["data"]
                return {
                    "url": qr_data["url"],
                    "qrcode_key": qr_data["qrcode_key"],
                }
            else:
                logger.warning("qrcode generate failed: %s", data.get("message"))
                return None
        except Exception as e:
            logger.error("qrcode generate error: %s", e)
            return None

    def poll_qrcode(self, qrcode_key: str) -> dict:
        """轮询扫码状态，返回 {status, cookie_data?, message?}
        status: "pending" | "scanned" | "expired" | "success" | "error"

        B站 poll 接口返回格式：
          {"code": 0, "message": "0", "data": {"code": 86101/86090/86038/0, ...}}
        真正的扫码状态码在 data.code 里，顶层 code 始终为 0（表示 HTTP API 成功）。
        """
        try:
            resp = self.session.get(
                "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
                params={"qrcode_key": qrcode_key},
                timeout=10,
            )
            data = resp.json()
            inner = data.get("data", {})
            # 真正的扫码状态码在 data.code 里
            inner_code = inner.get("code")
            logger.debug("qrcode poll: top_code=%s inner_code=%s message=%s",
                        data.get("code"), inner_code, inner.get("message", data.get("message")))

            if data.get("code") != 0:
                # 顶层 API 调用失败
                return {"status": "error", "message": data.get("message", "接口调用失败")}

            if inner_code == 0:
                # 扫码成功（data.code == 0）
                return {
                    "status": "success",
                    "cookie_data": inner,
                }
            elif inner_code == 86038:
                # 二维码已过期
                return {"status": "expired", "message": "二维码已过期，请刷新重试"}
            elif inner_code == 86090:
                # 已扫码但未确认
                return {"status": "scanned", "message": "已扫码，请在手机上确认"}
            elif inner_code == 86101:
                # 未扫码
                return {"status": "pending", "message": "等待扫码"}
            else:
                return {"status": "error", "message": inner.get("message", data.get("message", f"未知错误 code={inner_code}"))}
        except Exception as e:
            logger.error("qrcode poll error: %s", e)
            return {"status": "error", "message": str(e)}

    def apply_qrcode_cookie(self, cookie_data: dict) -> bool:
        """扫码成功后，将返回的 cookie 信息设置到 session 中，并返回是否登录成功"""
        # B站扫码登录返回的 cookie 信息包含 token 等
        # 直接通过 /x/passport-login/web/qrcode/poll 接口的 Set-Cookie 已经自动写入了
        # 但有时需要手动设置
        refresh_token = cookie_data.get("refresh_token", "")
        if refresh_token:
            self.session.cookies.set("refresh_token", refresh_token, domain=".bilibili.com")

        # 重新验证登录状态
        self._mid = None
        self._wbi_img_key = ""
        self._wbi_sub_key = ""
        mid = self.get_self_mid()
        return mid is not None

    def get_qrcode_image(self, url: str) -> bytes | None:
        """根据二维码 URL 获取二维码图片的 PNG 二进制数据"""
        try:
            # 使用独立 session，不携带现有 cookie（避免干扰）
            img_session = requests.Session()
            img_session.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.bilibili.com/",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            })
            resp = img_session.get(url, timeout=10)
            logger.info("qrcode image download: status=%s content-length=%s content-type=%s",
                        resp.status_code,
                        resp.headers.get("Content-Length", "?"),
                        resp.headers.get("Content-Type", "?"))
            if resp.status_code == 200 and resp.content:
                # 检查是否为图片
                if resp.content[:4] == b'\x89PNG' or resp.content[:2] == b'\xff\xd8':
                    return resp.content
                # 如果不是图片，可能是重定向页面，尝试用 qrcode 库生成
                logger.warning("qrcode url returned non-image content, will generate locally")
            return None
        except Exception as e:
            logger.error("get_qrcode_image error: %s", e)
            return None

    def generate_qrcode_locally(self, qrcode_key: str) -> bytes | None:
        """使用 qrcode_key 在本地生成二维码图片"""
        try:
            import qrcode as _qrcode
            from qrcode.image.pil import PilImage
        except ImportError:
            logger.error("qrcode library not installed, please run: pip install qrcode[pil]")
            return None

        try:
            # 构造 B站扫码登录 URL
            login_url = f"https://account.bilibili.com/h5/account-h5/auth/scan-web?navhide=1&callback=close&qrcode_key={qrcode_key}"
            qr = _qrcode.QRCode(
                version=1,
                error_correction=_qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(login_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            logger.error("generate_qrcode_locally error: %s", e)
            return None





