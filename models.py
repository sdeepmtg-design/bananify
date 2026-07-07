from dataclasses import dataclass


@dataclass(frozen=True)
class ImageModel:
    model_id: str
    title: str
    short_title: str
    description: str
    credit_cost: int = 1


# All models below are OpenRouter image models. Keep model_id values exactly as OpenRouter slugs.
IMAGE_MODELS: dict[str, ImageModel] = {
    "pro": ImageModel(
        model_id="google/gemini-3-pro-image",
        title="🍌 Nano Banana Pro",
        short_title="Nano Banana Pro",
        description="Максимальное качество, лучше для сложных сцен, текста на изображениях и редактирования.",
        credit_cost=1,
    ),
    "banana2": ImageModel(
        model_id="google/gemini-3.1-flash-image-preview",
        title="⚡ Nano Banana 2",
        short_title="Nano Banana 2",
        description="Быстрая генерация и редактирование, хороший баланс качества и скорости.",
        credit_cost=1,
    ),
    "flash": ImageModel(
        model_id="google/gemini-2.5-flash-image",
        title="🚀 Nano Banana Flash",
        short_title="Nano Banana Flash",
        description="Быстрая и экономичная модель для простых генераций и правок.",
        credit_cost=1,
    ),
}

DEFAULT_MODEL_KEY = "pro"


def get_model(model_key: str | None) -> ImageModel:
    return IMAGE_MODELS.get(model_key or DEFAULT_MODEL_KEY) or IMAGE_MODELS[DEFAULT_MODEL_KEY]
