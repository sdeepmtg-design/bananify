import asyncio
import logging
import time
from typing import Any

from fastapi import FastAPI, Request, HTTPException

from core.config import settings
from database.store import (
    admin_stats,
    get_user_settings,
    init_db,
    log_generation,
    set_aspect_ratio,
    set_image_count,
    set_last_prompt,
    touch_user,
)
from keyboards.inline import aspect_keyboard, count_keyboard, main_menu_keyboard
from services.openrouter import generate_images, user_friendly_error
from services.telegram import (
    answer_callback,
    download_file,
    edit_message_text,
    get_file,
    send_chat_action,
    send_message,
    send_photo,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_title)
generation_semaphore = asyncio.Semaphore(settings.max_parallel_generations)


@app.on_event("startup")
def on_startup():
    init_db()
    if not settings.telegram_token:
        logger.warning("TELEGRAM_TOKEN is not set")
    if not settings.openrouter_api_key:
        logger.warning("OPENROUTER_API_KEY is not set")
    logger.info("Bot started")


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "Telegram image bot is running",
        "webhook_path": f"/webhook/{settings.webhook_secret}",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    if secret != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    update = await request.json()
    logger.info("Telegram update received")

    if callback_query := update.get("callback_query"):
        asyncio.create_task(handle_callback(callback_query))
        return {"ok": True}

    message = update.get("message") or update.get("edited_message")
    if message:
        asyncio.create_task(handle_message(message))

    return {"ok": True}


async def handle_callback(callback: dict[str, Any]) -> None:
    try:
        callback_id = callback.get("id")
        data = callback.get("data") or ""
        message = callback.get("message") or {}
        chat_id = message.get("chat", {}).get("id")
        message_id = message.get("message_id")
        user_id = callback.get("from", {}).get("id")

        if callback_id:
            await asyncio.to_thread(answer_callback, settings.telegram_token, callback_id)
        if not chat_id or not user_id:
            return

        touch_user(user_id)
        user_settings = get_user_settings(user_id)

        if data == "menu:main":
            await asyncio.to_thread(
                edit_message_text,
                settings.telegram_token,
                chat_id,
                message_id,
                start_text(user_settings),
                main_menu_keyboard(),
            )
        elif data == "menu:create":
            await asyncio.to_thread(
                send_message,
                settings.telegram_token,
                chat_id,
                "🎨 Напиши описание картинки одним сообщением.\n\nНапример: кот-космонавт на Марсе, cinematic, ultra detailed",
            )
        elif data == "menu:edit":
            await asyncio.to_thread(
                send_message,
                settings.telegram_token,
                chat_id,
                "🖼 Отправь фото и добавь подпись, что с ним сделать.\n\nНапример: сделай это фото в стиле Pixar, сохрани лицо и позу.",
            )
        elif data == "menu:examples":
            await asyncio.to_thread(send_message, settings.telegram_token, chat_id, examples_text())
        elif data == "menu:help":
            await asyncio.to_thread(send_message, settings.telegram_token, chat_id, help_text())
        elif data in {"settings:aspect", "settings:format", "menu:aspect", "menu:format"}:
            await asyncio.to_thread(
                send_message,
                settings.telegram_token,
                chat_id,
                "📐 Выбери формат изображения:",
                aspect_keyboard(user_settings["aspect_ratio"]),
            )
        elif data in {"settings:n", "settings:count", "menu:n", "menu:count"}:
            await asyncio.to_thread(
                send_message,
                settings.telegram_token,
                chat_id,
                "🔢 Сколько изображений генерировать за один запрос?",
                count_keyboard(user_settings["image_count"]),
            )
        elif data.startswith("aspect:"):
            aspect = data.split(":", 1)[1]
            set_aspect_ratio(user_id, aspect)
            updated_settings = get_user_settings(user_id)
            await asyncio.to_thread(
                send_message,
                settings.telegram_token,
                chat_id,
                f"✅ Формат установлен: {aspect}\n\n" + start_text(updated_settings),
                main_menu_keyboard(),
            )
        elif data.startswith("n:"):
            count = int(data.split(":", 1)[1])
            set_image_count(user_id, count)
            updated_settings = get_user_settings(user_id)
            await asyncio.to_thread(
                send_message,
                settings.telegram_token,
                chat_id,
                f"✅ Количество изображений: {count}\n\n" + start_text(updated_settings),
                main_menu_keyboard(),
            )
    except Exception:
        logger.exception("Callback handling failed")


async def handle_message(message: dict[str, Any]) -> None:
    chat_id = message.get("chat", {}).get("id")
    user_id = message.get("from", {}).get("id")
    text = (message.get("text") or message.get("caption") or "").strip()
    photos = message.get("photo") or []

    if not chat_id or not user_id:
        return

    touch_user(user_id)
    user_settings = get_user_settings(user_id)

    if text.startswith("/start"):
        await asyncio.to_thread(send_message, settings.telegram_token, chat_id, start_text(user_settings), main_menu_keyboard())
        return

    if text.startswith("/help"):
        await asyncio.to_thread(send_message, settings.telegram_token, chat_id, help_text(), main_menu_keyboard())
        return

    if text.startswith("/examples"):
        await asyncio.to_thread(send_message, settings.telegram_token, chat_id, examples_text())
        return

    if text.startswith("/admin_stats"):
        await handle_admin_stats(chat_id, user_id)
        return

    if not text and photos:
        await asyncio.to_thread(
            send_message,
            settings.telegram_token,
            chat_id,
            "🖼 Фото получил. Теперь отправь фото ещё раз с подписью, что нужно изменить.\n\nНапример: замени фон на ночной Токио.",
        )
        return

    if not text:
        await asyncio.to_thread(
            send_message,
            settings.telegram_token,
            chat_id,
            "Отправь текстовое описание картинки 🎨",
            main_menu_keyboard(),
        )
        return

    if len(text) > settings.max_prompt_chars:
        await asyncio.to_thread(
            send_message,
            settings.telegram_token,
            chat_id,
            f"⚠️ Описание слишком длинное. Максимум: {settings.max_prompt_chars} символов.",
        )
        return

    reference_image = None
    if photos:
        try:
            biggest = photos[-1]
            file_info = await asyncio.to_thread(get_file, settings.telegram_token, biggest["file_id"])
            file_path = file_info["result"]["file_path"]
            reference_image = await asyncio.to_thread(download_file, settings.telegram_token, file_path)
        except Exception:
            logger.exception("Failed to download Telegram photo")
            await asyncio.to_thread(send_message, settings.telegram_token, chat_id, "⚠️ Не смог скачать фото из Telegram. Попробуй ещё раз.")
            return

    asyncio.create_task(process_generation(chat_id, user_id, text, reference_image))


async def process_generation(chat_id: int, user_id: int, prompt: str, reference_image: bytes | None = None) -> None:
    user_settings = get_user_settings(user_id)
    aspect_ratio = user_settings["aspect_ratio"]
    image_count = int(user_settings["image_count"])
    set_last_prompt(user_id, prompt)

    await asyncio.to_thread(
        send_message,
        settings.telegram_token,
        chat_id,
        f"⏳ Генерирую...\nФормат: {aspect_ratio}\nКоличество: {image_count}\n\nЗапросы обрабатываются по очереди.",
    )

    started_at = time.monotonic()
    async with generation_semaphore:
        try:
            await asyncio.to_thread(send_chat_action, settings.telegram_token, chat_id, "upload_photo")
            result = await asyncio.to_thread(
                generate_images,
                settings.openrouter_api_key,
                prompt,
                settings.openrouter_model,
                aspect_ratio,
                "1K",
                image_count,
                reference_image,
            )

            duration_ms = int((time.monotonic() - started_at) * 1000)
            log_generation(
                user_id=user_id,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_count=len(result.images),
                status="success",
                cost=result.cost,
                duration_ms=duration_ms,
            )

            for index, image in enumerate(result.images, start=1):
                caption = "Готово ✅" if len(result.images) == 1 else f"Готово ✅ {index}/{len(result.images)}"
                await asyncio.to_thread(send_photo, settings.telegram_token, chat_id, image, caption)
        except Exception as error:
            logger.exception("Image generation failed")
            error_code, message = user_friendly_error(error)
            duration_ms = int((time.monotonic() - started_at) * 1000)
            log_generation(
                user_id=user_id,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_count=image_count,
                status="failed",
                duration_ms=duration_ms,
                error_code=error_code,
            )
            await asyncio.to_thread(send_message, settings.telegram_token, chat_id, message)


async def handle_admin_stats(chat_id: int, user_id: int) -> None:
    if user_id not in settings.admin_user_ids:
        await asyncio.to_thread(send_message, settings.telegram_token, chat_id, "⛔ Эта команда доступна только админу.")
        return

    stats = admin_stats()
    errors = stats["recent_errors"]
    error_text = "нет" if not errors else "\n".join([f"• {code}: {count}" for code, count in errors])
    text = (
        "📊 Admin statistics\n\n"
        f"👤 Пользователей: {stats['total_users']}\n"
        f"🖼 Успешных генераций: {stats['total_generations']}\n"
        f"📅 Генераций за 24ч: {stats['today_generations']}\n"
        f"⚠️ Ошибок: {stats['failed_generations']}\n"
        f"💰 Примерная стоимость: ${stats['total_cost']:.4f}\n"
        f"⏱ Среднее время: {stats['avg_ms'] // 1000} сек.\n\n"
        f"Последние ошибки:\n{error_text}"
    )
    await asyncio.to_thread(send_message, settings.telegram_token, chat_id, text)


def start_text(user_settings: dict[str, Any]) -> str:
    return (
        "🍌 Привет! Я создаю изображения через Nano Banana Pro.\n\n"
        "Просто напиши, что нужно нарисовать. Также можешь отправить фото с подписью — я попробую его отредактировать.\n\n"
        f"Текущие настройки:\n📐 Формат: {user_settings['aspect_ratio']}\n🔢 Количество: {user_settings['image_count']}"
    )


def help_text() -> str:
    return (
        "ℹ️ Как пользоваться ботом:\n\n"
        "1. Напиши описание картинки — бот создаст изображение.\n"
        "2. Отправь фото с подписью — бот попробует отредактировать фото по описанию.\n"
        "3. Через кнопки можно выбрать формат и количество изображений.\n\n"
        "Команды:\n/start — главное меню\n/help — помощь\n/examples — примеры\n/admin_stats — статистика только для админа"
    )


def examples_text() -> str:
    return (
        "💡 Примеры запросов:\n\n"
        "• Белый кот в скафандре на Луне, cinematic, ultra detailed\n"
        "• Логотип для кофейни в минималистичном стиле\n"
        "• Футуристический город ночью, неон, дождь, 16:9\n"
        "• Персонаж для игры: маленький робот-садовник, 3D icon\n"
        "• Обложка трека в стиле synthwave, яркие цвета\n\n"
        "Для фото: отправь изображение с подписью вроде «сделай в стиле Pixar» или «замени фон на пляж»."
    )
