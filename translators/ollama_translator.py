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


class OllamaTranslator(Translator):
    def __init__(self, api_key: str = None, model: str = "llama3", base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = kwargs.get("ollama_model", model)
        self.base_url = kwargs.get("ollama_url", base_url)

    @property
    def api_url(self):
        return f"{self.base_url}/api/chat"

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        try:
            resp = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are a translator. Translate {source_lang} text to {target_lang}. Reply ONLY with the translation, no explanations.",
                        },
                        {"role": "user", "content": text},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.3},
                },
                timeout=60,
            )
            if resp.status_code != 200:
                return TranslationResult("", text, "ollama", success=False, error=_extract_error(resp))
            data = resp.json()
            translated = data["message"]["content"].strip()
            return TranslationResult(translated, text, "ollama")
        except Exception as e:
            return TranslationResult("", text, "ollama", success=False, error=str(e))
