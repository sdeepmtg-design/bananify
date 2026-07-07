import base64
import json
from dataclasses import dataclass
from typing import Any

import requests

OPENROUTER_IMAGES_URL = "https://openrouter.ai/api/v1/images"


class OpenRouterError(RuntimeError):
    def __init__(self, status_code: int | None, message: str, code: str | None = None):
        self.status_code = status_code
        self.code = code
        super().__init__(message)


@dataclass
class ImageGenerationResult:
    images: list[bytes]
    cost: float = 0.0
    raw_usage: dict[str, Any] | None = None


def _extract_error(response: requests.Response) -> tuple[str, str | None]:
    try:
        data = response.json()
        error = data.get("error", {})
        return str(error.get("message") or response.text[:500]), str(error.get("code") or response.status_code)
    except Exception:
        return response.text[:500], str(response.status_code)


def _data_url(image_bytes: bytes, media_type: str = "image/jpeg") -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{media_type};base64,{encoded}"


def generate_images(
    api_key: str,
    prompt: str,
    model: str,
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
    n: int = 1,
    reference_image: bytes | None = None,
    reference_media_type: str = "image/jpeg",
) -> ImageGenerationResult:
    if not api_key:
        raise OpenRouterError(None, "OPENROUTER_API_KEY is missing", "missing_api_key")

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "n": max(1, min(int(n), 4)),
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
    }

    if reference_image:
        payload["input_references"] = [
            {
                "type": "image_url",
                "image_url": {"url": _data_url(reference_image, reference_media_type)},
            }
        ]

    try:
        response = requests.post(
            OPENROUTER_IMAGES_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://render.com",
                "X-Title": "Telegram Nano Banana Pro Bot",
            },
            json=payload,
            timeout=220,
        )
    except requests.Timeout as exc:
        raise OpenRouterError(None, "OpenRouter request timed out", "timeout") from exc
    except requests.RequestException as exc:
        raise OpenRouterError(None, f"Network error: {exc}", "network_error") from exc

    if not response.ok:
        message, code = _extract_error(response)
        raise OpenRouterError(response.status_code, message, code)

    try:
        data = response.json()
        images = [base64.b64decode(item["b64_json"]) for item in data.get("data", []) if item.get("b64_json")]
        usage = data.get("usage") or {}
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise OpenRouterError(response.status_code, "Unexpected OpenRouter response", "bad_response") from exc

    if not images:
        raise OpenRouterError(response.status_code, "OpenRouter returned no images", "empty_response")

    return ImageGenerationResult(images=images, cost=float(usage.get("cost") or 0), raw_usage=usage)


def user_friendly_error(error: Exception) -> tuple[str, str]:
    text = str(error)
    code = getattr(error, "code", None) or "unknown_error"
    status = getattr(error, "status_code", None)
    combined = f"{code} {text}".lower()

    if "prohibited_content" in combined or "blocked" in combined:
        return (
            "prohibited_content",
            "⚠️ Модель отклонила этот запрос по правилам безопасности.\n\n"
            "Попробуй переформулировать описание: убери насилие, сексуальный контент, шокирующие детали, документы, обман или известных людей.",
        )
    if status == 402 or "insufficient credits" in combined:
        return ("insufficient_credits", "⚠️ На балансе OpenRouter недостаточно credits для генерации.")
    if status in (401, 403) or "api key" in combined or "auth" in combined:
        return ("auth_error", "⚠️ Ошибка авторизации OpenRouter. Проверь OPENROUTER_API_KEY в Render Environment.")
    if status == 429 or "rate" in combined:
        return ("rate_limit", "⚠️ Слишком много запросов. Подожди немного и попробуй снова.")
    if status and status >= 500:
        return ("provider_error", "⚠️ Провайдер временно недоступен. Попробуй ещё раз через пару минут.")
    if "timeout" in combined:
        return ("timeout", "⚠️ Генерация заняла слишком много времени. Попробуй ещё раз или упрости запрос.")
    return ("unknown_error", "⚠️ Не удалось создать изображение. Попробуй изменить описание или повторить позже.")
