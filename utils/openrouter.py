import base64
import json
from dataclasses import dataclass
from typing import Optional

import requests

OPENROUTER_IMAGES_URL = "https://openrouter.ai/api/v1/images"


@dataclass
class OpenRouterImageError(Exception):
    """Readable OpenRouter error used by the Telegram bot."""

    status_code: int
    message: str
    code: Optional[str] = None
    raw: Optional[str] = None

    def __str__(self) -> str:
        if self.code:
            return f"OpenRouter error {self.status_code} ({self.code}): {self.message}"
        return f"OpenRouter error {self.status_code}: {self.message}"


class OpenRouterResponseError(RuntimeError):
    pass


def _parse_openrouter_error(response: requests.Response) -> OpenRouterImageError:
    raw_text = response.text[:1500]
    message = raw_text or "Unknown OpenRouter error"
    code = None

    try:
        payload = response.json()
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        if isinstance(error, dict):
            message = error.get("message") or message
            code = str(error.get("code")) if error.get("code") is not None else None
    except json.JSONDecodeError:
        pass

    return OpenRouterImageError(
        status_code=response.status_code,
        message=message,
        code=code,
        raw=raw_text,
    )


def generate_image(
    api_key: str,
    prompt: str,
    model: str = "google/gemini-3-pro-image",
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
) -> bytes:
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing")

    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("Prompt is empty")

    try:
        response = requests.post(
            OPENROUTER_IMAGES_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://render.com",
                "X-Title": "Telegram Nano Banana Pro Bot",
            },
            json={
                "model": model,
                "prompt": prompt,
                "n": 1,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
            },
            timeout=180,
        )
    except requests.Timeout as exc:
        raise OpenRouterResponseError("OpenRouter request timed out") from exc
    except requests.RequestException as exc:
        raise OpenRouterResponseError(f"OpenRouter connection error: {exc}") from exc

    if not response.ok:
        raise _parse_openrouter_error(response)

    try:
        data = response.json()
        b64_image = data["data"][0]["b64_json"]
        return base64.b64decode(b64_image)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise OpenRouterResponseError(
            f"Unexpected OpenRouter response: {response.text[:1000]}"
        ) from exc
