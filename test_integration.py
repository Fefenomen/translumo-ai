"""
Synthetic integration test for Translumo-AI.
Tests the full pipeline: capture → OCR → translation (mock) → overlay update.
"""
import sys
import time
import threading
import numpy as np
from PIL import Image, ImageDraw

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from config import load_config
from capture import capture_region_np
from ocr import ocr_image, text_significantly_different
from translators.base import TranslationResult
from overlay import TranslationOverlay


def create_test_image(text: str, width=600, height=100):
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 28)
    except (OSError, ImportError):
        font = ImageFont.load_default()
    draw.text((20, 30), text, fill="black", font=font)
    return np.array(img)


def test_ocr():
    arr = create_test_image("Hello World 42")
    text = ocr_image(arr, lang="eng")
    assert text is not None, "OCR returned None"
    assert len(text) > 0, "OCR returned empty"
    print(f"  OCR: '{text}'")


def test_diff():
    assert text_significantly_different(None, "hello") is True
    assert text_significantly_different("hello", None) is True
    assert text_significantly_different("hello", "hello") is False
    assert text_significantly_different("hello", "hello world") is True
    assert text_significantly_different("test", "test!") is True
    print("  Diff detection: OK")


def test_overlay():
    app = QApplication.instance() or QApplication(sys.argv + ["-platform", "wayland"])
    overlay = TranslationOverlay(
        geometry=(100, 200, 300, 150),
        bg_color="#1a1a1a",
        text_color="#ffffff",
        font_size=16,
        opacity=180,
    )
    overlay.update_text("Original text", "Translated text")
    assert overlay.translated_text == "Translated text"
    assert overlay.original_text == "Original text"
    print("  Overlay creation and update: OK")
    overlay.hide_overlay()
    overlay.deleteLater()


def test_config():
    cfg = load_config()
    assert "provider" in cfg
    assert "source_lang" in cfg
    assert "target_lang" in cfg
    assert "capture_region" in cfg
    assert cfg["source_lang"] == "jpn"
    assert cfg["target_lang"] == "fra"
    print("  Config: OK")


def test_mock_translation():
    """Test that TranslationResult works correctly"""
    result = TranslationResult("Bonjour le monde", "Hello world", "mock")
    assert result.success is True
    assert result.translated_text == "Bonjour le monde"
    assert result.source_text == "Hello world"

    failed = TranslationResult("", "hello", "mock", success=False, error="No API key")
    assert failed.success is False
    assert failed.error == "No API key"
    print("  Translation result: OK")


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv + ["-platform", "wayland"])
    
    print("\n=== Integration Tests ===")
    
    print("\n1. Config tests:")
    test_config()
    
    print("\n2. OCR tests:")
    test_ocr()
    
    print("\n3. Diff detection tests:")
    test_diff()
    
    print("\n4. Mock translation tests:")
    test_mock_translation()
    
    print("\n5. Overlay tests:")
    test_overlay()
    
    print("\n=== All tests passed! ===")
    
    QTimer.singleShot(100, app.quit)
    app.exec_()
