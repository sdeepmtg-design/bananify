from dataclasses import dataclass


@dataclass(frozen=True)
class CreditPackage:
    package_id: str
    title: str
    credits: int
    stars: int
    description: str


# Telegram Stars amounts are integer XTR units.
PACKAGES: dict[str, CreditPackage] = {
    "pack_10": CreditPackage("pack_10", "🟢 Start — 10 AI-кредитов", 10, 300, "Пакет Start: 10 AI-кредитов"),
    "pack_50": CreditPackage("pack_50", "🔥 Plus — 50 AI-кредитов", 50, 1350, "Пакет Plus: 50 AI-кредитов"),
    "pack_100": CreditPackage("pack_100", "💎 PRO — 100 AI-кредитов", 100, 2500, "Пакет PRO: 100 AI-кредитов"),
}

# Backward compatibility for old callback data if a user clicks an older message.
PACKAGES["pack_30"] = PACKAGES["pack_50"]


def get_package(package_id: str) -> CreditPackage | None:
    return PACKAGES.get(package_id)
