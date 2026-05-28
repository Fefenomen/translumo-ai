from .base import Translator, TranslationResult
from .openai_translator import OpenAITranslator
from .anthropic_translator import AnthropicTranslator
from .mistral_translator import MistralTranslator
from .gemini_translator import GeminiTranslator
from .ollama_translator import OllamaTranslator

TRANSLATOR_MAP = {
    "openai": OpenAITranslator,
    "anthropic": AnthropicTranslator,
    "mistral": MistralTranslator,
    "gemini": GeminiTranslator,
    "ollama": OllamaTranslator,
}


def get_translator(provider: str, api_key: str = None, **kwargs):
    cls = TRANSLATOR_MAP.get(provider)
    if cls is None:
        raise ValueError(f"Unknown translator: {provider}")
    return cls(api_key=api_key, **kwargs)
