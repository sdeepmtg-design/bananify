def main_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "🎨 Создать изображение", "callback_data": "menu:create"},
                {"text": "🖼 Редактировать фото", "callback_data": "menu:edit"},
            ],
            [
                {"text": "📐 Формат", "callback_data": "settings:aspect"},
                {"text": "🔢 Количество", "callback_data": "settings:n"},
            ],
            [
                {"text": "🤖 Модель", "callback_data": "settings:model"},
                {"text": "👤 Профиль", "callback_data": "menu:profile"},
            ],
            [
                {"text": "💳 Купить кредиты", "callback_data": "menu:buy"},
            ],
            [
                {"text": "💡 Примеры", "callback_data": "menu:examples"},
                {"text": "ℹ️ Помощь", "callback_data": "menu:help"},
            ],
        ]
    }


def aspect_keyboard(current: str = "1:1") -> dict:
    options = [
        ("🟦 1:1", "1:1"),
        ("📱 9:16", "9:16"),
        ("🖥 16:9", "16:9"),
        ("📄 3:4", "3:4"),
        ("🖼 4:3", "4:3"),
    ]
    rows = []
    for label, value in options:
        prefix = "✅ " if current == value else ""
        rows.append([{"text": prefix + label, "callback_data": f"aspect:{value}"}])
    rows.append([{"text": "⬅️ Назад", "callback_data": "menu:main"}])
    return {"inline_keyboard": rows}


def count_keyboard(current: int = 1) -> dict:
    rows = []
    for value in [1, 2, 3, 4]:
        prefix = "✅ " if current == value else ""
        rows.append([{"text": f"{prefix}{value} изображение(я)", "callback_data": f"n:{value}"}])
    rows.append([{"text": "⬅️ Назад", "callback_data": "menu:main"}])
    return {"inline_keyboard": rows}




def buy_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "🟢 Start — 10 кредитов / 300 ⭐", "callback_data": "buy:start"}],
            [{"text": "🔥 Plus — 50 кредитов / 1350 ⭐", "callback_data": "buy:plus"}],
            [{"text": "💎 PRO — 100 кредитов / 2500 ⭐", "callback_data": "buy:pro"}],
            [{"text": "⬅️ Назад", "callback_data": "menu:main"}],
        ]
    }


def model_keyboard(current: str = "pro") -> dict:
    from models import IMAGE_MODELS

    rows = []
    for key, model in IMAGE_MODELS.items():
        prefix = "✅ " if current == key else ""
        rows.append([{
            "text": f"{prefix}{model.title} — {model.credit_cost} кредит",
            "callback_data": f"model:{key}",
        }])
    rows.append([{"text": "⬅️ Назад", "callback_data": "menu:main"}])
    return {"inline_keyboard": rows}
