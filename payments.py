from dataclasses import dataclass


@dataclass(frozen=True)
class CreditPackage:
    package_id: str
    title: str
    credits: int
    stars: int
    description: str


# Telegram Stars amounts are integer XTR units.
# 1 credit = 1 generated/edited image in the default pricing model.
PACKAGES: dict[str, CreditPackage] = {
    "start": CreditPackage("start", "🟢 Start — 10 кредитов", 10, 300, "10 AI-кредитов для генерации или редактирования изображений"),
    "plus": CreditPackage("plus", "🔥 Plus — 50 кредитов", 50, 1350, "50 AI-кредитов. Самый удобный пакет для регулярного использования"),
    "pro": CreditPackage("pro", "💎 PRO — 100 кредитов", 100, 2500, "100 AI-кредитов для активных пользователей"),
}


def get_package(package_id: str) -> CreditPackage | None:
    return PACKAGES.get(package_id)
