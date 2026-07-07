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
                {"text": "💳 Купить изображения", "callback_data": "menu:buy"},
                {"text": "👤 Профиль", "callback_data": "menu:profile"},
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
            [{"text": "10 изображений — 600 ⭐", "callback_data": "buy:pack_10"}],
            [{"text": "30 изображений — 1500 ⭐", "callback_data": "buy:pack_30"}],
            [{"text": "100 изображений — 4000 ⭐", "callback_data": "buy:pack_100"}],
            [{"text": "⬅️ Назад", "callback_data": "menu:main"}],
        ]
    }
