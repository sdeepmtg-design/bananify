import os
import logging
from fastapi import FastAPI, Request, HTTPException

from utils.openrouter import generate_image
from utils.telegram_api import send_message, send_photo, send_chat_action

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change-me-secret")
MODEL = os.environ.get("OPENROUTER_IMAGE_MODEL", "google/gemini-3-pro-image")

if not TELEGRAM_TOKEN:
    logger.warning("TELEGRAM_TOKEN is not set")
if not OPENROUTER_API_KEY:
    logger.warning("OPENROUTER_API_KEY is not set")

app = FastAPI(title="Telegram Nano Banana Pro Bot")


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "Telegram image bot is running",
        "webhook_path": f"/webhook/{WEBHOOK_SECRET}",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    update = await request.json()
    logger.info("Telegram update received")

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return {"ok": True}

    if not text:
        send_message(TELEGRAM_TOKEN, chat_id, "Отправь текстовое описание картинки 🎨")
        return {"ok": True}

    if text.startswith("/start"):
        send_message(
            TELEGRAM_TOKEN,
            chat_id,
            "Привет! Я создаю картинки через Nano Banana Pro.\n\n"
            "Просто напиши, что нарисовать. Например:\n"
            "Кот-космонавт на Марсе, cinematic, ultra detailed",
        )
        return {"ok": True}

    if text.startswith("/help"):
        send_message(
            TELEGRAM_TOKEN,
            chat_id,
            "Команды:\n"
            "/start — запуск\n"
            "/help — помощь\n\n"
            "Для генерации просто отправь описание изображения.",
        )
        return {"ok": True}

    try:
        send_message(TELEGRAM_TOKEN, chat_id, "⏳ Генерирую изображение...")
        send_chat_action(TELEGRAM_TOKEN, chat_id, "upload_photo")

        image_bytes = generate_image(
            api_key=OPENROUTER_API_KEY,
            prompt=text,
            model=MODEL,
            aspect_ratio="1:1",
            resolution="1K",
        )

        send_photo(
            TELEGRAM_TOKEN,
            chat_id,
            image_bytes,
            caption="Готово ✅",
        )
    except Exception as error:
        logger.exception("Image generation failed")
        send_message(
            TELEGRAM_TOKEN,
            chat_id,
            "Не получилось создать изображение 😕\n"
            f"Ошибка: {error}",
        )

    return {"ok": True}
