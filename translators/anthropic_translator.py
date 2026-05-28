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


class AnthropicTranslator(Translator):
    def __init__(self, api_key: str = None, model: str = "claude-3-5-haiku-latest", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        if not self.api_key:
            return TranslationResult("", text, "anthropic", success=False, error="No API key")
        try:
            resp = requests.post(
                self.api_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "system": f"You are a translator. Translate {source_lang} text to {target_lang}. Reply ONLY with the translation, no explanations.",
                    "messages": [{"role": "user", "content": text}],
                },
                timeout=30,
            )
            if resp.status_code != 200:
                return TranslationResult("", text, "anthropic", success=False, error=_extract_error(resp))
            data = resp.json()
            translated = data["content"][0]["text"].strip()
            return TranslationResult(translated, text, "anthropic")
        except Exception as e:
            return TranslationResult("", text, "anthropic", success=False, error=str(e))
