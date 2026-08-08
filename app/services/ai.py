from dataclasses import dataclass
from typing import Protocol

from app.config import Settings
from app.schemas import AIOutput


@dataclass(frozen=True)
class ImageInput:
    data: bytes
    mime_type: str


class AIProvider(Protocol):
    name: str

    def analyze(self, images: list[ImageInput], category_slugs: list[str]) -> AIOutput:
        ...


class StubAIProvider:
    name = "stub"

    def analyze(self, images: list[ImageInput], category_slugs: list[str]) -> AIOutput:
        return AIOutput(
            category_slug="other" if "other" in category_slugs else category_slugs[0],
            confidence=0.0,
            summary=f"Demo analysis for {len(images)} image(s); configure Gemini for real results.",
            detected_text=[],
        )


class GeminiAIProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def analyze(self, images: list[ImageInput], category_slugs: list[str]) -> AIOutput:
        from google.genai import types

        prompt = (
            "Analyze these photos of one second-hand item. Identify the item, read all visible "
            "text such as brands, labels, and sizes, and choose exactly one category slug from: "
            f"{', '.join(category_slugs)}. Return a concise factual summary. Do not invent text "
            "that is not visible."
        )
        contents = [prompt]
        contents.extend(
            types.Part.from_bytes(data=image.data, mime_type=image.mime_type) for image in images
        )
        response_schema = AIOutput.model_json_schema()
        response_schema["properties"]["category_slug"]["enum"] = category_slugs
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_json_schema=response_schema,
            ),
        )
        if response.parsed is not None:
            output = AIOutput.model_validate(response.parsed)
        else:
            output = AIOutput.model_validate_json(response.text)
        if output.category_slug not in category_slugs:
            raise ValueError("AI returned a category outside the allowed taxonomy")
        return output


def build_ai_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "stub":
        return StubAIProvider()
    if settings.ai_provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required when AI_PROVIDER=gemini")
        return GeminiAIProvider(settings.gemini_api_key, settings.gemini_model)
    if settings.gemini_api_key:
        return GeminiAIProvider(settings.gemini_api_key, settings.gemini_model)
    return StubAIProvider()
