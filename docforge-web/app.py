"""
DocForge — 주제만 넣으면 문서(+선택 이미지) 생성 웹앱.
실행: cd docforge-web && uvicorn app:app --reload --port 8765
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_a, **_k):
        return False

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from services import image_gen
from services import svg_gen
from services import text_gen
from services import web_import
from services.image_gen import AVAILABLE_MODELS, MODEL_PRIORITY
from services.text_gen import excerpt_limit_for_tier, generate_svg_specs_async
from services.markdown_images import inject_images_into_markdown, strip_placeholder_images
from services.prompt_config import get_builtin_defaults, get_for_api, reset_to_defaults, save_prompts
from services.publish import (
    content_target_info, delete_static_image, has_data_images, list_posts,
    load_post, publish_bundle, publish_markdown, save_static_images, suggest_filename,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
for _base in (ROOT, ROOT.parent):
    _env = _base / ".env"
    if _env.exists():
        load_dotenv(_env)
        break

app = FastAPI(title="DocForge", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateBody(BaseModel):
    topic: str = Field(..., min_length=1, max_length=24000)
    template: str = Field("blog", pattern="^(blog|philosophy|plain|tutorial|review|comparison|troubleshoot|weekly|news|prompt_eng)$")
    with_images: bool = False
    max_images: int = Field(2, ge=0, le=4)
    with_svg: bool = False
    max_svg: int = Field(2, ge=0, le=6)
    length: str = Field("medium", pattern="^(short|medium|long|very_long)$")
    image_hints: str | None = Field(None, max_length=3000)


class ImageSaveItem(BaseModel):
    filename: str = Field(..., max_length=200)
    mime: str = Field("image/png", max_length=50)
    data_base64: str


class PublishBody(BaseModel):
    """Hugo `content/posts` 에 마크다운 저장."""

    markdown: str = Field(..., min_length=1, max_length=5_000_000)
    filename: str | None = Field(None, max_length=240)
    slug_hint: str | None = Field(None, max_length=200)
    subfolder: str | None = Field(
        None,
        max_length=128,
        description="posts 바로 아래 하위 폴더 (예: software-dev). 비우면 posts 루트.",
    )
    images: list[ImageSaveItem] | None = Field(None, description="저장할 이미지 목록")


class PromptsUpdateBody(BaseModel):
    """비어 있지 않은 필드만 저장에 반영."""

    blog: str | None = None
    philosophy: str | None = None
    plain: str | None = None
    tutorial: str | None = None
    review: str | None = None
    comparison: str | None = None
    troubleshoot: str | None = None
    weekly: str | None = None
    news: str | None = None
    prompt_eng: str | None = None
    document_user: str | None = None
    image_prompt_generator: str | None = None


def _api_key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or "").strip()


def _models_payload() -> dict:
    """UI에 표시할 모델 메타데이터."""
    image_chain = []
    for i, key in enumerate(MODEL_PRIORITY, start=1):
        info = AVAILABLE_MODELS[key]
        image_chain.append(
            {
                "order": i,
                "key": key,
                "id": info["id"],
                "label": info["label"],
                "type": info["type"],
            }
        )
    return {
        "text": {
            "document_and_prompts": text_gen.TEXT_MODEL,
            "note": "본문 마크다운·삽화용 영문 프롬프트 문장 생성에 동일 모델 사용",
        },
        "image": {
            "strategy": "순차 시도: 앞 모델이 실패하면 다음으로 폴백 (AiVS DebateImageService와 동일)",
            "chain": image_chain,
        },
    }


@app.get("/api/prompts")
def api_get_prompts():
    """편집기용: 현재 적용 중인 프롬프트 + 플레이스홀더 안내."""
    return get_for_api()


@app.get("/api/prompts/builtins")
def api_prompts_builtins():
    """코드에 내장된 기본 프롬프트 (되돌리기 미리보기)."""
    return {"prompts": get_builtin_defaults()}


@app.post("/api/prompts")
def api_save_prompts(body: PromptsUpdateBody):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "저장할 필드가 없습니다. 최소 한 칸 이상 보내 주세요.")
    try:
        save_prompts(updates)
    except ValueError as e:
        raise HTTPException(400, f"플레이스홀더 오류: {e}") from e
    except Exception as e:
        raise HTTPException(500, str(e)) from e
    return {"ok": True, "prompts": get_for_api()["prompts"]}


@app.post("/api/prompts/reset")
def api_reset_prompts():
    """user_prompts.json 삭제 후 기본값."""
    reset_to_defaults()
    return {"ok": True, "prompts": get_for_api()["prompts"]}


@app.get("/api/content-target")
def api_content_target():
    """저장 대상 `content/posts` 경로와 쓰기 가능 여부."""
    return content_target_info()


@app.post("/api/publish-post")
def api_publish_post(body: PublishBody):
    """검토·편집한 마크다운을 블로그 `content/posts` 에 UTF-8로 저장."""
    info = content_target_info()
    if not info["writable"]:
        raise HTTPException(
            503,
            f"해당 폴더에 쓸 수 없습니다: {info['posts_dir']}",
        )
    hint = (body.slug_hint or "").strip() or "post"
    use_bundle = has_data_images(body.markdown)
    try:
        if use_bundle:
            path, fname, rel_display, sub_used = publish_bundle(
                body.markdown,
                body.filename,
                hint,
                body.subfolder or "",
            )
        else:
            path, fname, rel_display, sub_used = publish_markdown(
                body.markdown,
                body.filename,
                hint,
                body.subfolder or "",
            )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except OSError as e:
        logger.exception("게시물 저장 실패")
        raise HTTPException(500, str(e)) from e
    # 에셋 이미지 → static/images/posts/<slug>/ 에 저장
    saved_images = []
    if body.images:
        slug = fname.replace(".md", "") if fname else (body.slug_hint or "post")
        saved_images = save_static_images(
            [img.model_dump() for img in body.images], slug
        )

    return {
        "ok": True,
        "path": str(path),
        "filename": fname,
        "relative_path": rel_display,
        "subfolder": sub_used,
        "posts_dir": info["posts_dir"],
        "bundle": use_bundle,
        "saved_images": saved_images,
    }


@app.get("/api/posts")
def api_list_posts(subfolder: str = ""):
    """포스트 목록 (카테고리별)."""
    return {"posts": list_posts(subfolder)}


@app.get("/api/post")
def api_load_post(path: str):
    """기존 포스트 로드 (마크다운 + 연결 이미지)."""
    try:
        data = load_post(path)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return data


@app.delete("/api/post-image")
def api_delete_post_image(slug: str, filename: str):
    """static/images/posts/<slug>/<filename> 삭제."""
    ok = delete_static_image(slug, filename)
    if not ok:
        raise HTTPException(404, "이미지를 찾을 수 없습니다.")
    return {"ok": True}


class SuggestCategoryBody(BaseModel):
    topic: str = Field(..., min_length=1, max_length=5000)


@app.post("/api/suggest-category")
async def suggest_category(body: SuggestCategoryBody):
    """주제를 보고 적절한 카테고리를 추천."""
    key = _api_key()
    if not key:
        raise HTTPException(503, "GEMINI_API_KEY가 설정되지 않았습니다.")

    categories = content_target_info().get("subfolders", [])
    if not categories:
        raise HTTPException(422, "카테고리 폴더가 없습니다.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    prompt = f"""다음 카테고리 목록 중에서 주제에 가장 적합한 카테고리 하나만 골라줘.
반드시 목록에 있는 이름 그대로 한 단어만 답해. 설명 없이 카테고리 이름만.

카테고리 목록: {', '.join(categories)}

주제: {body.topic[:2000]}"""

    try:
        resp = await client.aio.models.generate_content(
            model=text_gen.TEXT_MODEL,
            config=types.GenerateContentConfig(
                max_output_tokens=64,
                temperature=0.1,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
            contents=prompt,
        )
        suggestion = resp.text.strip().lower().replace(" ", "-")
        # 목록에 있는지 확인
        if suggestion not in categories:
            # 부분 매칭 시도
            for cat in categories:
                if cat in suggestion or suggestion in cat:
                    suggestion = cat
                    break
            else:
                suggestion = categories[0]
    except Exception as e:
        logger.warning("카테고리 추천 실패: %s", e)
        suggestion = categories[0]

    return {"category": suggestion}


@app.get("/api/health")
def health():
    k = _api_key()
    return {
        "ok": True,
        "gemini_configured": bool(k),
        "service": "docforge",
        "models": _models_payload(),
    }


class ImportUrlBody(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)


@app.post("/api/import-url")
async def import_url(body: ImportUrlBody):
    """URL에서 콘텐츠를 가져와 Gemini로 다듬어 반환. 이미지는 원본 그대로."""
    key = _api_key()
    if not key:
        raise HTTPException(503, "GEMINI_API_KEY가 설정되지 않았습니다.")

    t0 = time.perf_counter()
    try:
        raw_text, images = await web_import.fetch_page(body.url)
    except Exception as e:
        logger.exception("URL 가져오기 실패: %s", body.url)
        raise HTTPException(502, f"URL 가져오기 실패: {e}") from e

    if not raw_text.strip():
        raise HTTPException(422, "페이지에서 텍스트를 추출할 수 없습니다.")

    try:
        markdown = await web_import.rewrite_text(raw_text, key, url=body.url)
    except Exception as e:
        logger.exception("텍스트 다듬기 실패")
        raise HTTPException(500, f"텍스트 다듬기 실패: {e}") from e

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    images_out = []
    for i, img in enumerate(images):
        images_out.append({
            "index": i,
            "prompt": img.get("url", ""),
            "model": "원본",
            "mime": img["mime"],
            "data_base64": img["data_base64"],
        })

    slug = _slug_from_topic(body.url)
    return {
        "ok": True,
        "topic": body.url,
        "template": "import",
        "length": "medium",
        "markdown": markdown,
        "images": images_out,
        "image_prompts": [img.get("url", "") for img in images],
        "svgs": [],
        "models": _models_payload(),
        "suggested_filename": suggest_filename(markdown, slug),
        "manifest": {
            "slug": slug,
            "elapsed_ms": elapsed_ms,
            "image_count": len(images_out),
            "svg_count": 0,
        },
    }


class SingleImageBody(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=3000)
    aspect_ratio: str = Field("16:9", pattern="^(1:1|16:9|9:16|4:3|3:4)$")


@app.post("/api/generate-image")
async def generate_single_image(body: SingleImageBody):
    """단일 이미지 생성 (프롬프트 → 이미지 1장)."""
    key = _api_key()
    if not key:
        raise HTTPException(503, "GEMINI_API_KEY가 설정되지 않았습니다.")
    try:
        data, label, mime = await image_gen.generate_one_image_async(
            key, body.prompt, aspect_ratio=body.aspect_ratio
        )
    except Exception as e:
        logger.exception("단일 이미지 생성 실패")
        raise HTTPException(500, str(e)) from e
    b64 = base64.standard_b64encode(data).decode("ascii")
    return {
        "ok": True,
        "image": {
            "prompt": body.prompt,
            "model": label,
            "mime": mime,
            "data_base64": b64,
        },
    }


class SvgBody(BaseModel):
    description: str = Field(..., min_length=1, max_length=2000)
    svg_type: str = Field("architecture", pattern="^(architecture|infographic|icon)$")
    style: str = Field("modern", pattern="^(modern|minimal|colorful|dark)$")


@app.post("/api/generate-svg")
async def generate_svg(body: SvgBody):
    key = _api_key()
    if not key:
        raise HTTPException(503, "GEMINI_API_KEY가 설정되지 않았습니다.")
    try:
        svg_code = await svg_gen.generate_svg_async(
            key, body.description, body.svg_type, body.style
        )
    except Exception as e:
        logger.exception("SVG 생성 실패")
        raise HTTPException(500, str(e)) from e
    return {"ok": True, "svg": svg_code, "type": body.svg_type, "style": body.style}


@app.post("/api/generate")
async def generate(body: GenerateBody):
    topic = body.topic.strip()
    if not topic:
        raise HTTPException(400, "주제가 비어 있습니다.")

    key = _api_key()
    if not key:
        raise HTTPException(
            503,
            "GEMINI_API_KEY가 설정되지 않았습니다. 프로젝트 루트 또는 docforge-web/.env 에 키를 넣어 주세요.",
        )

    t0 = time.perf_counter()
    try:
        markdown = await text_gen.generate_document_async(
            topic, body.template, key, length_tier=body.length
        )
    except Exception as e:
        logger.exception("텍스트 생성 실패")
        raise HTTPException(500, str(e)) from e

    images_out: list[dict] = []
    image_prompts_used: list[str] = []
    if body.with_images and body.max_images > 0:
        excerpt_cap = excerpt_limit_for_tier(body.length)
        try:
            prompts = await text_gen.generate_image_prompts_async(
                topic,
                markdown,
                body.max_images,
                key,
                excerpt_max_chars=excerpt_cap,
                extra_hints=body.image_hints,
            )
        except Exception as e:
            logger.warning("이미지 프롬프트 생성 실패: %s", e)
            prompts = [
                f"Editorial illustration, conceptual, related to: {topic[:100]}"
            ] * min(body.max_images, 1)

        image_prompts_used = list(prompts[: body.max_images])
        for i, prompt in enumerate(prompts[: body.max_images]):
            try:
                data, label, mime = await image_gen.generate_one_image_async(
                    key, prompt, aspect_ratio="16:9"
                )
            except Exception as e:
                logger.warning("이미지 %s 실패: %s", i, e)
                data, label, mime = image_gen.generate_one_image(
                    "", prompt, aspect_ratio="16:9"
                )
            b64 = base64.standard_b64encode(data).decode("ascii")
            images_out.append(
                {
                    "index": i,
                    "prompt": prompt,
                    "model": label,
                    "mime": mime,
                    "data_base64": b64,
                }
            )

    # 가짜 경로(placeholder) 마크다운 → 깨진 이미지 방지
    if images_out:
        markdown = inject_images_into_markdown(markdown, images_out)
    else:
        markdown = strip_placeholder_images(markdown)

    # SVG 에셋 생성
    svgs_out: list[dict] = []
    if body.with_svg and body.max_svg > 0:
        excerpt_cap = excerpt_limit_for_tier(body.length)
        try:
            svg_specs = await generate_svg_specs_async(
                topic, markdown, body.max_svg, key, excerpt_max_chars=excerpt_cap
            )
        except Exception as e:
            logger.warning("SVG 스펙 생성 실패: %s", e)
            svg_specs = [{"type": "architecture", "style": "modern", "description": topic}] * min(body.max_svg, 1)

        for i, spec in enumerate(svg_specs[: body.max_svg]):
            try:
                svg_code = await svg_gen.generate_svg_async(
                    key,
                    spec.get("description", topic),
                    spec.get("type", "architecture"),
                    spec.get("style", "modern"),
                )
                svgs_out.append({
                    "index": i,
                    "type": spec.get("type", "architecture"),
                    "style": spec.get("style", "modern"),
                    "description": spec.get("description", ""),
                    "svg": svg_code,
                })
            except Exception as e:
                logger.warning("SVG %s 생성 실패: %s", i, e)

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    slug = _slug_from_topic(topic)
    suggested = suggest_filename(markdown, slug)
    return {
        "ok": True,
        "topic": topic,
        "template": body.template,
        "length": body.length,
        "markdown": markdown,
        "images": images_out,
        "image_prompts": image_prompts_used,
        "svgs": svgs_out,
        "models": _models_payload(),
        "suggested_filename": suggested,
        "manifest": {
            "slug": slug,
            "elapsed_ms": elapsed_ms,
            "image_count": len(images_out),
            "svg_count": len(svgs_out),
        },
    }


def _slug_from_topic(topic: str) -> str:
    s = re.sub(r"[^\w\s-]", "", topic.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")[:80]
    if len(s) < 2:
        s = "doc-" + hashlib.md5(topic.encode("utf-8")).hexdigest()[:12]
    return s


# 정적 파일은 /static 만 마운트 (루트에 StaticFiles를 두면 일부 환경에서 /api 와 충돌할 수 있음)
static_dir = ROOT / "static"


@app.get("/")
def read_index():
    """브라우저는 반드시 http://127.0.0.1:포트/ 로 열 것 (file:// 로 열면 API 연결 불가)."""
    index = static_dir / "index.html"
    if not index.is_file():
        raise HTTPException(500, "static/index.html 없음")
    return FileResponse(index)


@app.get("/edit")
def read_edit():
    edit = static_dir / "edit.html"
    if not edit.is_file():
        raise HTTPException(500, "static/edit.html 없음")
    return FileResponse(edit)


# 블로그 static/images/ 서빙 (미리보기에서 /images/posts/... 경로 해결)
blog_images_dir = ROOT.parent / "static" / "images"
if blog_images_dir.is_dir():
    app.mount("/images", StaticFiles(directory=str(blog_images_dir)), name="blog-images")

if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
