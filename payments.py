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
    "pack_10": CreditPackage("pack_10", "10 изображений", 10, 600, "Пакет на 10 генераций изображений"),
    "pack_30": CreditPackage("pack_30", "30 изображений", 30, 1500, "Пакет на 30 генераций изображений"),
    "pack_100": CreditPackage("pack_100", "100 изображений", 100, 4000, "Пакет на 100 генераций изображений"),
}


def get_package(package_id: str) -> CreditPackage | None:
    return PACKAGES.get(package_id)
