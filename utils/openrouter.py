import base64
import requests

OPENROUTER_IMAGES_URL = "https://openrouter.ai/api/v1/images"


def generate_image(
    api_key: str,
    prompt: str,
    model: str = "google/gemini-3-pro-image",
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
) -> bytes:
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing")

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

    if not response.ok:
        raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text[:500]}")

    data = response.json()

    try:
        b64_image = data["data"][0]["b64_json"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected OpenRouter response: {data}") from exc

    return base64.b64decode(b64_image)
