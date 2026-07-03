# Telegram Nano Banana Pro Bot

Telegram-бот для генерации изображений через OpenRouter и модель Nano Banana Pro.

## Что внутри

- FastAPI webhook-сервер
- Генерация изображений через OpenRouter `/api/v1/images`
- Отправка картинки пользователю в Telegram
- Готовый `render.yaml` для деплоя на Render
- Секреты через Environment Variables

## Переменные окружения

На Render добавь:

```env
TELEGRAM_TOKEN=твой_telegram_bot_token
OPENROUTER_API_KEY=твой_openrouter_key
WEBHOOK_SECRET=любой_длинный_секрет
OPENROUTER_IMAGE_MODEL=google/gemini-3-pro-image
```

## Локальный запуск

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Локально webhook Telegram без публичного URL работать не будет. Для тестов удобнее использовать Render или ngrok.

## Деплой на Render

1. Создай новый GitHub-репозиторий.
2. Загрузи туда эти файлы.
3. На Render выбери **New → Blueprint** или **New → Web Service**.
4. Подключи GitHub-репозиторий.
5. Добавь Environment Variables:
   - `TELEGRAM_TOKEN`
   - `OPENROUTER_API_KEY`
   - `WEBHOOK_SECRET`
   - `OPENROUTER_IMAGE_MODEL`
6. Нажми Deploy.

## Установка webhook

После деплоя Render даст URL вида:

```text
https://your-app-name.onrender.com
```

Открой в браузере:

```text
https://api.telegram.org/botTELEGRAM_TOKEN/setWebhook?url=https://your-app-name.onrender.com/webhook/WEBHOOK_SECRET
```

Замени:

- `TELEGRAM_TOKEN` на токен Telegram-бота
- `your-app-name` на имя сервиса Render
- `WEBHOOK_SECRET` на твой секрет из Render

Проверить webhook можно так:

```text
https://api.telegram.org/botTELEGRAM_TOKEN/getWebhookInfo
```

## Важно

Не коммить `.env`, Telegram token и OpenRouter key в GitHub.
Все ключи храни только в Render → Environment Variables.
