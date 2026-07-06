import logging
import os

from fastapi import FastAPI, HTTPException, Request

from utils.openrouter import OpenRouterImageError, OpenRouterResponseError, generate_image
from utils.telegram_api import send_chat_action, send_message, send_photo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change-me-secret")
MODEL = os.environ.get("OPENROUTER_IMAGE_MODEL", "google/gemini-3-pro-image")
DEFAULT_ASPECT_RATIO = os.environ.get("DEFAULT_ASPECT_RATIO", "1:1")
DEFAULT_RESOLUTION = os.environ.get("DEFAULT_RESOLUTION", "1K")
MAX_PROMPT_LENGTH = int(os.environ.get("MAX_PROMPT_LENGTH", "1500"))

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
        safe_send_message(chat_id, "Отправь текстовое описание картинки 🎨")
        return {"ok": True}

    if text.startswith("/start"):
        safe_send_message(
            chat_id,
            "Привет! Я создаю картинки через Nano Banana Pro 🍌🎨\n\n"
            "Просто напиши, что нарисовать. Например:\n"
            "• кот-космонавт на Марсе, cinematic, ultra detailed\n"
            "• логотип кофейни в минималистичном стиле\n"
            "• футуристический город ночью, neon lights\n\n"
            "Команда /help покажет подсказки.",
        )
        return {"ok": True}

    if text.startswith("/help"):
        safe_send_message(
            chat_id,
            "Как пользоваться:\n\n"
            "1. Отправь описание картинки одним сообщением.\n"
            "2. Лучше указывай стиль, детали, фон и формат.\n"
            "3. Если запрос отклонён, переформулируй его мягче.\n\n"
            "Пример:\n"
            "\"Панда-диджей на космической вечеринке, 3D, яркие цвета, 1:1\"",
        )
        return {"ok": True}

    if len(text) > MAX_PROMPT_LENGTH:
        safe_send_message(
            chat_id,
            f"Описание слишком длинное. Сократи его до {MAX_PROMPT_LENGTH} символов и попробуй снова.",
        )
        return {"ok": True}

    try:
        safe_send_message(chat_id, "⏳ Генерирую изображение... Обычно это занимает немного времени.")
        safe_send_chat_action(chat_id, "upload_photo")

        image_bytes = generate_image(
            api_key=OPENROUTER_API_KEY,
            prompt=text,
            model=MODEL,
            aspect_ratio=DEFAULT_ASPECT_RATIO,
            resolution=DEFAULT_RESOLUTION,
        )

        safe_send_photo(
            chat_id,
            image_bytes,
            caption="Готово ✅",
        )
    except OpenRouterImageError as error:
        logger.exception("OpenRouter rejected image generation")
        safe_send_message(chat_id, user_friendly_openrouter_error(error))
    except OpenRouterResponseError:
        logger.exception("OpenRouter response/connection failed")
        safe_send_message(
            chat_id,
            "⚠️ OpenRouter временно не ответил или вернул неожиданный ответ. Попробуй ещё раз чуть позже.",
        )
    except Exception:
        logger.exception("Image generation failed")
        safe_send_message(
            chat_id,
            "⚠️ Не удалось сгенерировать изображение. Попробуй изменить описание или повторить позже.",
        )

    return {"ok": True}


def user_friendly_openrouter_error(error: OpenRouterImageError) -> str:
    combined = f"{error.code or ''} {error.message}".lower()

    if error.status_code == 402 or "insufficient credits" in combined:
        return "⚠️ На балансе OpenRouter недостаточно средств для генерации изображения."

    if "prohibited_content" in combined or "blocked" in combined:
        return (
            "⚠️ Модель отклонила этот запрос по правилам безопасности.\n\n"
            "Попробуй переформулировать описание без шокирующих деталей, насилия, сексуального контента, "
            "документов, обмана, deepfake или запрещённых тем."
        )

    if error.status_code == 429 or "rate" in combined:
        return "⚠️ Слишком много запросов. Подожди немного и попробуй снова."

    if error.status_code in {401, 403}:
        return "⚠️ Ошибка доступа к OpenRouter. Проверь API-ключ в настройках Render."

    if error.status_code >= 500:
        return "⚠️ На стороне OpenRouter или провайдера модели временная ошибка. Попробуй позже."

    return "⚠️ Запрос не удалось обработать. Попробуй изменить описание картинки и отправить ещё раз."


def safe_send_message(chat_id: int, text: str):
    try:
        return send_message(TELEGRAM_TOKEN, chat_id, text)
    except Exception:
        logger.exception("Failed to send Telegram message")
        return None


def safe_send_photo(chat_id: int, image_bytes: bytes, caption: str = ""):
    try:
        return send_photo(TELEGRAM_TOKEN, chat_id, image_bytes, caption)
    except Exception:
        logger.exception("Failed to send Telegram photo")
        safe_send_message(chat_id, "⚠️ Картинка была создана, но Telegram не смог её отправить.")
        return None


def safe_send_chat_action(chat_id: int, action: str):
    try:
        return send_chat_action(TELEGRAM_TOKEN, chat_id, action)
    except Exception:
        logger.warning("Failed to send Telegram chat action", exc_info=True)
        return None
