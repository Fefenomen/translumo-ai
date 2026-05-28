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


class GeminiTranslator(Translator):
    def __init__(self, api_key: str = None, model: str = "gemini-2.0-flash", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model

    @property
    def api_url(self):
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        if not self.api_key:
            return TranslationResult("", text, "gemini", success=False, error="No API key")
        try:
            resp = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": f"Translate the following text from {source_lang} to {target_lang}. Reply ONLY with the translation, no explanations. Text: {text}"
                                }
                            ]
                        }
                    ],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024},
                },
                timeout=30,
            )
            if resp.status_code != 200:
                return TranslationResult("", text, "gemini", success=False, error=_extract_error(resp))
            data = resp.json()
            translated = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return TranslationResult(translated, text, "gemini")
        except Exception as e:
            return TranslationResult("", text, "gemini", success=False, error=str(e))
