from io import BytesIO
import requests


def _url(token: str, method: str) -> str:
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is missing")
    return f"https://api.telegram.org/bot{token}/{method}"


def api_call(token: str, method: str, payload: dict | None = None, timeout: int = 30):
    response = requests.post(_url(token, method), json=payload or {}, timeout=timeout)
    response.raise_for_status()
    return response.json()


def send_message(token: str, chat_id: int, text: str, reply_markup: dict | None = None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api_call(token, "sendMessage", payload)


def edit_message_text(token: str, chat_id: int, message_id: int, text: str, reply_markup: dict | None = None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api_call(token, "editMessageText", payload)


def answer_callback(token: str, callback_query_id: str, text: str = ""):
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    return api_call(token, "answerCallbackQuery", payload)


def send_photo(token: str, chat_id: int, image_bytes: bytes, caption: str = ""):
    response = requests.post(
        _url(token, "sendPhoto"),
        data={"chat_id": chat_id, "caption": caption},
        files={"photo": ("image.png", BytesIO(image_bytes), "image/png")},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def send_chat_action(token: str, chat_id: int, action: str):
    return api_call(token, "sendChatAction", {"chat_id": chat_id, "action": action})


def get_file(token: str, file_id: str) -> dict:
    return api_call(token, "getFile", {"file_id": file_id})


def download_file(token: str, file_path: str) -> bytes:
    response = requests.get(f"https://api.telegram.org/file/bot{token}/{file_path}", timeout=60)
    response.raise_for_status()
    return response.content


def send_invoice(token: str, chat_id: int, title: str, description: str, payload: str, stars: int):
    # Для Telegram Stars используется currency=XTR и пустой provider_token.
    invoice_payload = {
        "chat_id": chat_id,
        "title": title,
        "description": description,
        "payload": payload,
        "provider_token": "",
        "currency": "XTR",
        "prices": [{"label": title, "amount": int(stars)}],
    }
    return api_call(token, "sendInvoice", invoice_payload)


def answer_pre_checkout_query(token: str, pre_checkout_query_id: str, ok: bool = True, error_message: str | None = None):
    payload = {"pre_checkout_query_id": pre_checkout_query_id, "ok": ok}
    if error_message:
        payload["error_message"] = error_message
    return api_call(token, "answerPreCheckoutQuery", payload)
