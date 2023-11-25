import httpx
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Protocol, Optional, Tuple


from nonebot.adapters.onebot.v11 import MessageSegment


async def search_qq(keyword: str) -> Optional[MessageSegment]:
    url = "https://c.y.qq.com/splcloud/fcgi-bin/smartbox_new.fcg"
    params = {
        "format": "json",
        "inCharset": "utf-8",
        "outCharset": "utf-8",
        "notice": 0,
        "platform": "yqq.json",
        "needNewCode": 0,
        "uin": 0,
        "hostUin": 0,
        "is_xml": 0,
        "key": keyword,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        result = resp.json()
    songs: List[Dict[str, str]] = result["data"]["song"]["itemlist"]
    if songs:
        songs.sort(
            key=lambda x: SequenceMatcher(None, keyword, x["name"]).ratio(),
            reverse=True,
        )
        return MessageSegment.music("qq", int(songs[0]["id"]))


async def search_163(keyword: str) -> Optional[MessageSegment]:
    url = "https://music.163.com/api/cloudsearch/pc"
    params = {"s": keyword, "type": 1, "offset": 0}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, params=params)
        result = resp.json()
    songs: List[Dict[str, Any]] = result["result"]["songs"]
    if songs:
        songs.sort(
            key=lambda x: SequenceMatcher(None, keyword, x["name"]).ratio(),
            reverse=True,
        )
        return MessageSegment.music("163", songs[0]["id"])


async def search_bili(keyword: str) -> Optional[MessageSegment]:
    search_url = "https://api.bilibili.com/audio/music-service-c/s"
    params = {"page": 1, "pagesize": 1,
              "search_type": "music", "keyword": keyword}
    async with httpx.AsyncClient() as client:
        resp = await client.get(search_url, params=params)
        result = resp.json()
    songs: List[Dict[str, Any]] = result["data"]["result"]
    if songs:
        songs.sort(
            key=lambda x: SequenceMatcher(None, keyword, x["title"]).ratio(),
            reverse=True,
        )
        info = songs[0]
        return MessageSegment.text(f"https://www.bilibili.com/audio/au{info['id']}")


class Func(Protocol):
    async def __call__(self, keyword: str) -> Optional[MessageSegment]:
        ...


@dataclass
class Source:
    name: str
    keywords: Tuple[str, ...]
    func: Func


sources = [
    Source("网易云音乐", ("牛牛163点歌", "牛牛网易点歌", "牛牛网易云点歌"), search_163),
    Source("QQ音乐", ("牛牛qq点歌", "牛牛QQ点歌"), search_qq),
    Source("B站音频区", ("牛牛bili点歌", "牛牛bilibili点歌",
           "牛牛b站点歌", "牛牛B站点歌"), search_bili),
]
