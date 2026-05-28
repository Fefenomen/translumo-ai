from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TranslationResult:
    translated_text: str
    source_text: str
    provider: str
    success: bool = True
    error: Optional[str] = None


class Translator(ABC):
    def __init__(self, api_key: str = None, **kwargs):
        self.api_key = api_key

    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        pass

    def build_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
        return (
            f"Translate the following text from {source_lang} to {target_lang}. "
            f"Return ONLY the translated text, nothing else. "
            f"Keep the translation natural and accurate. "
            f"If the text is already in {target_lang}, return it as-is.\n\n"
            f"Text: {text}"
        )
