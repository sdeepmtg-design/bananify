# Telegram Nano Banana Pro Bot

Telegram-бот для генерации изображений через OpenRouter Image API и модель Nano Banana Pro.

## Что умеет

- Генерация изображений по текстовому описанию.
- Редактирование/перегенерация по фото: пользователь отправляет фото с подписью, бот передает его как reference image.
- Inline-кнопки: создание, редактирование, примеры, помощь.
- Выбор формата: `1:1`, `9:16`, `16:9`, `3:4`, `4:3`.
- Выбор количества изображений: 1–4.
- Очередь генераций через `MAX_PARALLEL_GENERATIONS`.
- Нормальная обработка ошибок OpenRouter: credits, prohibited content, rate limit, auth, timeout.
- Админ-статистика через `/admin_stats` только для пользователей из `ADMIN_USER_IDS`.
- Статистика хранится в SQLite. Изображения на диск не сохраняются.

## Переменные окружения

В Render → Environment добавь:

```env
TELEGRAM_TOKEN=your_telegram_bot_token
OPENROUTER_API_KEY=your_openrouter_api_key
WEBHOOK_SECRET=your_secret_webhook_path
ADMIN_USER_IDS=123456789
OPENROUTER_IMAGE_MODEL=google/gemini-3-pro-image
MAX_PARALLEL_GENERATIONS=2
MAX_PROMPT_CHARS=1800
DB_PATH=bot_data.sqlite3
```

`ADMIN_USER_IDS` — это Telegram user ID админа. Можно указать несколько через запятую:

```env
ADMIN_USER_IDS=111111111,222222222
```

## Render

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Установка webhook

После деплоя открой в браузере:

```text
https://api.telegram.org/bot<TELEGRAM_TOKEN>/setWebhook?url=https://<RENDER_URL>/webhook/<WEBHOOK_SECRET>
```

Проверка:

```text
https://api.telegram.org/bot<TELEGRAM_TOKEN>/getWebhookInfo
```

## Команды бота

- `/start` — главное меню
- `/help` — помощь
- `/examples` — примеры запросов
- `/admin_stats` — статистика только для админа

## Важно

Не коммить реальные ключи в GitHub. Используй только переменные окружения Render.


## Fix notes

- Кнопки «Формат» и «Количество» отправляют отдельное сообщение с inline-выбором, чтобы не зависеть от редактирования старого сообщения Telegram.
- Команда `/admin_stats` продолжает работать только для `ADMIN_USER_IDS`, но не показывается в тексте помощи для обычных пользователей.
