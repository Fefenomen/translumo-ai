import json
import os
from typing import Optional

CONFIG_DIR = os.path.expanduser("~/.config/translumo-ai")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "capture_region": None,
    "source_lang": "jpn",
    "target_lang": "fra",
    "ocr_lang": "jpn+eng",
    "capture_interval_ms": 800,
    "provider": "ollama",
    "api_keys": {
        "openai": "",
        "anthropic": "",
        "mistral": "",
        "gemini": "",
    },
    "ollama_url": "http://localhost:11434",
    "ollama_model": "aya:8b",
    "overlay_opacity": 180,
    "overlay_font_size": 16,
    "overlay_bg_color": "#1a1a1a",
    "overlay_text_color": "#ffffff",
}


def load_config() -> dict:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def get_api_key(provider: str) -> Optional[str]:
    cfg = load_config()
    return cfg.get("api_keys", {}).get(provider, "") or None
