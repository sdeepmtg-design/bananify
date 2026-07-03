from io import BytesIO
import requests


def _telegram_url(token: str, method: str) -> str:
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is missing")
    return f"https://api.telegram.org/bot{token}/{method}"


def send_message(token: str, chat_id: int, text: str):
    response = requests.post(
        _telegram_url(token, "sendMessage"),
        json={"chat_id": chat_id, "text": text},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def send_photo(token: str, chat_id: int, image_bytes: bytes, caption: str = ""):
    response = requests.post(
        _telegram_url(token, "sendPhoto"),
        data={"chat_id": chat_id, "caption": caption},
        files={"photo": ("image.png", BytesIO(image_bytes), "image/png")},
        timeout=90,
    )
    response.raise_for_status()
    return response.json()


def send_chat_action(token: str, chat_id: int, action: str):
    response = requests.post(
        _telegram_url(token, "sendChatAction"),
        json={"chat_id": chat_id, "action": action},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
