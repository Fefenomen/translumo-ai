import requests
from .base import Translator, TranslationResult


class OpenAITranslator(Translator):
    def __init__(self, api_key: str = None, model: str = "gpt-4o", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        if not self.api_key:
            return TranslationResult("", text, "openai", success=False, error="No API key")
        try:
            resp = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                f"You are a translator. Translate {source_lang} text to {target_lang}. "
                                f"Reply ONLY with the translation, no explanations."
                            ),
                        },
                        {"role": "user", "content": text},
                    ],
                    "temperature": 0.3,
                },
                timeout=30,
            )
            data = resp.json()
            translated = data["choices"][0]["message"]["content"].strip()
            return TranslationResult(translated, text, "openai")
        except Exception as e:
            return TranslationResult("", text, "openai", success=False, error=str(e))
