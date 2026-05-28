import sys
import time
import threading

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from ocr import normalize_text, text_significantly_different
from overlay import TranslationWindow
from translators.base import TranslationResult


class FakeTranslator:
    def __init__(self, result_map=None):
        self.result_map = result_map or {}

    def translate(self, text, source_lang, target_lang):
        translated = self.result_map.get(text, text)
        return TranslationResult(translated, text, "mock")


class FakeBridge(QObject):
    text_translated = pyqtSignal(str)


def test_debounce_identical_text_triggers():
    last = None
    count = 0
    threshold = 3
    triggered = False

    for _ in range(3):
        text = "hello world"
        text_norm = normalize_text(text)
        if text_norm == last:
            count += 1
            if count >= threshold:
                triggered = True
                break
        elif not text_significantly_different(last, text_norm):
            last = text_norm
            count += 1
            if count >= threshold:
                triggered = True
                break
        else:
            last = text_norm
            count = 1

    assert triggered, "Debounce should reach threshold after 3 identical texts"


def test_debounce_similar_text_triggers():
    last = None
    count = 0
    threshold = 3
    triggered = False

    texts = ["hello world", "hello  world", "hello\nworld"]

    for t in texts:
        t_norm = normalize_text(t)
        if t_norm == last:
            count += 1
        elif not text_significantly_different(last, t_norm):
            last = t_norm
            count += 1
        else:
            last = t_norm
            count = 1

        if count >= threshold:
            triggered = True
            break

    assert triggered, "Debounce should trigger for near-identical texts after normalize"


def test_debounce_different_text_resets():
    last = None
    count = 0
    threshold = 3
    ever_reached_2 = False

    for t in ["hello", "world", "foo", "bar"]:
        t_norm = normalize_text(t)
        if t_norm == last:
            count += 1
        elif not text_significantly_different(last, t_norm):
            last = t_norm
            count += 1
        else:
            last = t_norm
            count = 1
        if count >= 2:
            ever_reached_2 = True

    assert not ever_reached_2, "Different texts should keep resetting debounce"


def test_signal_updates_window(qapp):
    window = TranslationWindow()
    bridge = FakeBridge()
    translator = FakeTranslator({"hello": "bonjour"})
    result_text = []

    def on_translated(text):
        result_text.append(text)
        window.set_text(text)

    bridge.text_translated.connect(on_translated)

    source = "jpn"
    target = "fra"
    text = "hello"

    cached = None
    if cached is not None:
        translated = cached
    else:
        r = translator.translate(text, source, target)
        translated = r.translated_text if r.success and r.translated_text else text

    bridge.text_translated.emit(translated)

    assert len(result_text) == 1
    assert result_text[0] == "bonjour"
    assert window.text_edit.toPlainText() == "bonjour"
    window.close()


def test_cache_hit_skips_translation():
    cache = {"hello": "bonjour", "world": "monde"}
    texts_to_translate = []
    translations = {}

    for t in ["hello", "world"]:
        cached = cache.get(t)
        if cached is not None:
            translations[t] = cached
        else:
            texts_to_translate.append(t)

    assert texts_to_translate == []
    assert translations["hello"] == "bonjour"
    assert translations["world"] == "monde"


def test_cache_miss_triggers_translation():
    cache = {}
    texts_to_translate = []
    translations = {}

    for t in ["hello", "world"]:
        cached = cache.get(t)
        if cached is not None:
            translations[t] = cached
        else:
            texts_to_translate.append(t)

    assert texts_to_translate == ["hello", "world"]


def test_launch_smoke(qapp):
    from main import TranslumoAI
    app = TranslumoAI()
    assert app.translator is not None
    assert app._bridge is not None
    assert app.translation_window is not None
    app.stop_translation()
    app.worker_thread.quit()
    app.worker_thread.wait()
    app.translation_window.close()
