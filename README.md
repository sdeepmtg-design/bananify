# Telegram Nano Banana Pro Bot

Telegram-бот для генерации изображений через OpenRouter Image API и модель Nano Banana Pro.

## Что умеет

- Генерация изображений по текстовому описанию.
- Редактирование/перегенерация по фото: пользователь отправляет фото с подписью, бот передает его как reference image.
- Inline-кнопки: создание, редактирование, формат, количество, покупка, профиль, примеры, помощь.
- Выбор формата: `1:1`, `9:16`, `16:9`, `3:4`, `4:3`.
- Выбор количества изображений: 1–4. OpenRouter получает `n=1`, а бот делает несколько отдельных запросов.
- 1 бесплатная генерация для каждого нового пользователя.
- Платные кредиты через Telegram Stars (`XTR`).
- Баланс пользователя через `/balance` или кнопку «Профиль».
- Очередь генераций через `MAX_PARALLEL_GENERATIONS`.
- Нормальная обработка ошибок OpenRouter: credits, prohibited content, rate limit, auth, timeout.
- Скрытая админ-статистика через `/admin_stats` только для пользователей из `ADMIN_USER_IDS`.
- Статистика, пользователи, платежи и кредиты хранятся в SQLite.

## Пакеты изображений

Настроены в `payments.py`:

- 🟢 Start — 10 кредитов / 300 ⭐
- 🔥 Plus — 50 кредитов / 1350 ⭐
- 💎 PRO — 100 кредитов / 2500 ⭐

1 изображение = 1 кредит. Если пользователь выбрал 4 изображения, спишется 4 кредита.

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
- `/balance` — баланс
- `/buy` — купить изображения
- `/paysupport` — поддержка платежей

Скрытая команда для админа:

- `/admin_stats` — статистика только для `ADMIN_USER_IDS`

## Важно

Не коммить реальные ключи в GitHub. Используй только переменные окружения Render.
