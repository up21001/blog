"""공개 웹 API로 기술 커뮤니티 트렌드 주제 수집 (별도 API 키 불필요).

- Hacker News: Firebase 공식 JSON API
- DEV Community: 공개 REST API

선택적으로 GEMINI_API_KEY로 제목을 한국어 블로그 주제 한 줄로 변환."""

from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .gemini_thinking import text_thinking_config

logger = logging.getLogger(__name__)

USER_AGENT = "DocForge/1.1 (tech blog authoring; contact: local)"

HN_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
DEVTO_ARTICLES = "https://dev.to/api/articles?per_page={n}&top=7"


def _fetch_json(url: str, timeout: float = 18.0) -> Any:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _hn_item(item_id: int) -> dict | None:
    try:
        data = _fetch_json(HN_ITEM.format(id=item_id), timeout=12.0)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        logger.debug("HN item %s 실패: %s", item_id, e)
        return None
    if not isinstance(data, dict):
        return None
    if data.get("deleted") or data.get("dead"):
        return None
    title = (data.get("title") or "").strip()
    if not title:
        return None
    url = (data.get("url") or "").strip()
    if not url:
        url = f"https://news.ycombinator.com/item?id={item_id}"
    score = data.get("score")
    if score is not None and not isinstance(score, int):
        try:
            score = int(score)
        except (TypeError, ValueError):
            score = None
    return {
        "source": "hacker_news",
        "title": title,
        "url": url,
        "score": score,
    }


def fetch_hacker_news(limit: int = 12) -> list[dict]:
    limit = max(1, min(limit, 40))
    try:
        ids = _fetch_json(HN_TOP, timeout=12.0)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        logger.warning("HN topstories 실패: %s", e)
        return []
    if not isinstance(ids, list):
        return []
    ids = [int(x) for x in ids[: max(limit * 2, limit + 8)] if str(x).isdigit()]
    id_to_row: dict[int, dict | None] = {}
    workers = min(10, max(4, limit))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_hn_item, i): i for i in ids}
        for fut in as_completed(futs):
            iid = futs[fut]
            try:
                id_to_row[iid] = fut.result()
            except Exception:
                id_to_row[iid] = None
    out: list[dict] = []
    for iid in ids:
        if len(out) >= limit:
            break
        row = id_to_row.get(iid)
        if row:
            out.append(row)
    return out


def fetch_devto(limit: int = 8) -> list[dict]:
    limit = max(1, min(limit, 20))
    url = DEVTO_ARTICLES.format(n=limit)
    try:
        raw = _fetch_json(url, timeout=15.0)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        logger.warning("DEV API 실패: %s", e)
        return []
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        title = (row.get("title") or "").strip()
        u = (row.get("url") or "").strip()
        if not title or not u:
            continue
        out.append({"source": "dev_to", "title": title, "url": u, "score": row.get("positive_reactions_count")})
        if len(out) >= limit:
            break
    return out


def _norm_key(title: str) -> str:
    t = title.lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t[:72]


def fetch_merged(total_limit: int = 18) -> tuple[list[dict], str]:
    """HN + DEV 병합, 제목 유사 시 한쪽만 유지."""
    total_limit = max(5, min(total_limit, 35))
    hn_n = max(6, int(total_limit * 0.55))
    dev_n = max(4, total_limit - hn_n)

    hn = fetch_hacker_news(hn_n)
    dev = fetch_devto(dev_n)

    seen: set[str] = set()
    merged: list[dict] = []

    def add_batch(rows: list[dict]) -> None:
        for r in rows:
            if len(merged) >= total_limit:
                return
            k = _norm_key(r["title"])
            if k in seen:
                continue
            seen.add(k)
            merged.append(
                {
                    "source": r["source"],
                    "title": r["title"],
                    "url": r["url"],
                    "score": r.get("score"),
                }
            )

    add_batch(hn)
    add_batch(dev)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return merged, ts


def add_korean_topics(items: list[dict], api_key: str) -> list[dict]:
    """각 항목에 topic_ko 필드 추가 (실패 시 원본 유지)."""
    if not items or not api_key:
        return items

    from google import genai
    from google.genai import types

    lines = "\n".join(f"{i}. {it['title']}" for i, it in enumerate(items))
    prompt = f"""다음은 기술 뉴스·커뮤니티 제목 목록이다. 각 번호에 대응하는 **한국어 블로그 글 주제**를 한 줄씩만 제안하라.

규칙:
- 기술 블로그에 바로 쓸 수 있는 주제 문장 (~하기, ~정리, ~비교, ~살펴보기 등)
- 원문 제목을 직역하지 말고 독자에게 주는 가치 중심으로 재구성
- 출력은 JSON 배열만 (설명·코드펜스 금지). 형식: [{{"i":0,"topic_ko":"..."}},{{"i":1,"topic_ko":"..."}}, ...]
- i는 0부터 {len(items) - 1}까지 순서대로, 빠짐없이

제목 목록:
{lines}"""

    client = genai.Client(api_key=api_key)
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.35,
                thinking_config=text_thinking_config(),
            ),
        )
        text = (resp.text or "").strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
        arr = json.loads(text)
        if not isinstance(arr, list):
            return items
        by_i: dict[int, str] = {}
        for el in arr:
            if not isinstance(el, dict):
                continue
            i = el.get("i")
            ko = (el.get("topic_ko") or "").strip()
            if isinstance(i, int) and ko:
                by_i[i] = ko
        out = []
        for idx, it in enumerate(items):
            row = dict(it)
            row["topic_ko"] = by_i.get(idx) or it["title"]
            out.append(row)
        return out
    except Exception as e:
        logger.warning("트렌드 한글화 실패: %s", e)
        return [{**it, "topic_ko": it["title"]} for it in items]
