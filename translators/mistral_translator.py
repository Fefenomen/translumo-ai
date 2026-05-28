import requests
from .base import Translator, TranslationResult


def _extract_error(resp):
    try:
        body = resp.json()
        err = body.get("error", {})
        if isinstance(err, dict):
            return err.get("message", resp.reason)
        return str(err)
    except Exception:
        return resp.reason


class MistralTranslator(Translator):
    def __init__(self, api_key: str = None, model: str = "mistral-large-latest", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
        self.api_url = "https://api.mistral.ai/v1/chat/completions"

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        if not self.api_key:
            return TranslationResult("", text, "mistral", success=False, error="No API key")
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
                            "content": f"You are a translator. Translate {source_lang} text to {target_lang}. Reply ONLY with the translation, no explanations.",
                        },
                        {"role": "user", "content": text},
                    ],
                    "temperature": 0.3,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                return TranslationResult("", text, "mistral", success=False, error=_extract_error(resp))
            data = resp.json()
            translated = data["choices"][0]["message"]["content"].strip()
            return TranslationResult(translated, text, "mistral")
        except Exception as e:
            return TranslationResult("", text, "mistral", success=False, error=str(e))
