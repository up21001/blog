"""
이미지 생성 — AiVS DebateImageService 패턴 (Imagen → Flash Image 폴백, Pillow 플레이스홀더).
"""

from __future__ import annotations

import asyncio
import base64
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# PIL 없을 때 최소 PNG (1×1)
_MIN_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

AVAILABLE_MODELS = {
    "imagen4ultra": {
        "id": "imagen-4.0-ultra-generate-001",
        "label": "Imagen 4 Ultra",
        "type": "imagen",
    },
    "imagen4": {
        "id": "imagen-4.0-generate-001",
        "label": "Imagen 4",
        "type": "imagen",
    },
    "imagen4fast": {
        "id": "imagen-4.0-fast-generate-001",
        "label": "Imagen 4 Fast",
        "type": "imagen",
    },
    "gemini-3-pro-image": {
        "id": "gemini-3-pro-image-preview",
        "label": "Gemini 3 Pro Image",
        "type": "gemini",
    },
    "gemini-flash-image": {
        "id": "gemini-2.5-flash-image",
        "label": "Gemini 2.5 Flash Image",
        "type": "gemini",
    },
}

# 프리셋별 이미지 모델 우선순위
IMAGE_PRESETS = {
    "fast": ["imagen4", "imagen4fast", "gemini-flash-image"],
    "quality": ["imagen4ultra", "imagen4", "gemini-flash-image"],
    "creative": ["gemini-3-pro-image", "imagen4", "gemini-flash-image"],
}

MODEL_PRIORITY = IMAGE_PRESETS["fast"]


def _pillow_placeholder(prompt: str, aspect_ratio: str = "16:9") -> bytes:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return _MIN_PNG

    w, h = (640, 360) if aspect_ratio == "16:9" else (512, 512)
    img = Image.new("RGB", (w, h), color=(32, 36, 48))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w - 1, h - 1], outline=(80, 90, 120), width=2)
    label = "[DocForge] GEMINI_API_KEY 또는 이미지 API 실패"
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    draw.text((w // 2, h // 2 - 20), label, fill=(180, 190, 210), font=font, anchor="mm")
    short = (prompt[:70] + "…") if len(prompt) > 70 else prompt
    draw.text((w // 2, h // 2 + 16), short, fill=(140, 150, 170), font=font, anchor="mm")
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _generate_with_model_sync(
    api_key: str, prompt: str, model_key: str, aspect_ratio: str, max_retries: int = 3
) -> Tuple[bytes, str]:
    import time

    from google import genai
    from google.genai import types

    model_info = AVAILABLE_MODELS[model_key]
    client = genai.Client(api_key=api_key)

    _backoff = [5, 15, 30]

    for attempt in range(max_retries):
        try:
            if model_info["type"] == "imagen":
                response = client.models.generate_images(
                    model=model_info["id"],
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio=aspect_ratio,
                    ),
                )
                if response.generated_images:
                    return response.generated_images[0].image.image_bytes, model_info["label"]
                raise RuntimeError(f"{model_info['label']}: 생성된 이미지 없음")

            response = client.models.generate_content(
                model=model_info["id"],
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    return part.inline_data.data, model_info["label"]
            raise RuntimeError(f"{model_info['label']}: 이미지 데이터 없음")

        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
            if not is_rate_limit:
                raise
            if attempt < max_retries - 1:
                wait = _backoff[attempt] if attempt < len(_backoff) else _backoff[-1]
                logger.warning(
                    "%s 429 rate limit (attempt %d/%d), retrying in %ds…",
                    model_info["label"], attempt + 1, max_retries, wait,
                )
                time.sleep(wait)
            else:
                logger.warning(
                    "%s 429 rate limit exhausted after %d retries — falling back",
                    model_info["label"], max_retries,
                )
                raise


def generate_one_image(
    api_key: str,
    prompt: str,
    aspect_ratio: str = "16:9",
    image_preset: str = "fast",
) -> Tuple[bytes, str, str]:
    """
    이미지 바이트, 모델 라벨, mime type 반환.
    실패 시 Pillow 플레이스홀더 PNG.
    """
    if not api_key:
        return _pillow_placeholder(prompt, aspect_ratio), "Placeholder", "image/png"

    priority = IMAGE_PRESETS.get(image_preset, MODEL_PRIORITY)
    last_err = None
    for idx, mk in enumerate(priority):
        try:
            data, label = _generate_with_model_sync(api_key, prompt, mk, aspect_ratio)
            return data, label, "image/png"
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
            if is_rate_limit and idx < len(priority) - 1:
                logger.warning(
                    "%s rate limit 소진 → %s 로 폴백",
                    AVAILABLE_MODELS[mk]["label"],
                    AVAILABLE_MODELS[priority[idx + 1]]["label"],
                )
            else:
                logger.warning("%s 실패: %s", AVAILABLE_MODELS[mk]["label"], e)
            last_err = e

    logger.warning("이미지 전 모델 실패 → 플레이스홀더: %s", last_err)
    return _pillow_placeholder(prompt, aspect_ratio), "Placeholder", "image/png"


async def generate_one_image_async(
    api_key: str, prompt: str, aspect_ratio: str = "16:9",
    image_preset: str = "fast",
) -> Tuple[bytes, str, str]:
    return await asyncio.to_thread(generate_one_image, api_key, prompt, aspect_ratio, image_preset)


async def generate_batch_images_async(
    api_key: str,
    prompts: list[str],
    aspect_ratio: str = "16:9",
    image_preset: str = "quality",
    delay_between: float = 3.0,
) -> list[Tuple[bytes, str, str]]:
    """Generate multiple images with delay between requests to avoid rate limits."""
    results = []
    for i, prompt in enumerate(prompts):
        if i > 0:
            await asyncio.sleep(delay_between)
        result = await generate_one_image_async(api_key, prompt, aspect_ratio, image_preset)
        results.append(result)
    return results
