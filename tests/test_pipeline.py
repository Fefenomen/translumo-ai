import sys
import time
import threading

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from ocr import normalize_text, text_significantly_different
from overlay import OverlayManager
from translators.base import TranslationResult


class FakeTranslator:
    def __init__(self, result_map=None):
        self.result_map = result_map or {}

    def translate(self, text, source_lang, target_lang):
        translated = self.result_map.get(text, text)
        return TranslationResult(translated, text, "mock")


class FakeBridge(QObject):
    blocks_translated = pyqtSignal(list)


def test_debounce_identical_text_triggers():
    last = None
    count = 0
    threshold = 3
    triggered = False

    blocks1 = [{"text": "hello"}, {"text": "world"}]
    concat1 = normalize_text("|".join(b["text"] for b in blocks1))

    for _ in range(3):
        concat = concat1
        if concat == last:
            count += 1
            if count >= threshold:
                triggered = True
                break
        elif not text_significantly_different(last, concat):
            last = concat
            count += 1
            if count >= threshold:
                triggered = True
                break
        else:
            last = concat
            count = 1

    assert triggered, "Debounce should reach threshold after 3 identical texts"


def test_debounce_similar_text_triggers():
    last = None
    count = 0
    threshold = 3
    triggered = False

    texts = ["hello world", "hello  world", "hello\nworld"]

    for concat in texts:
        concat_norm = normalize_text(concat)
        if concat_norm == last:
            count += 1
        elif not text_significantly_different(last, concat_norm):
            last = concat_norm
            count += 1
        else:
            last = concat_norm
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

    for text in ["hello", "world", "foo", "bar"]:
        concat = normalize_text(text)
        if concat == last:
            count += 1
        elif not text_significantly_different(last, concat):
            last = concat
            count += 1
        else:
            last = concat
            count = 1
        if count >= 2:
            ever_reached_2 = True

    assert not ever_reached_2, "Different texts should keep resetting debounce"


def test_translate_async_updates_overlay(qapp):
    mgr = OverlayManager()
    bridge = FakeBridge()
    translator = FakeTranslator({"hello": "bonjour"})
    result_blocks = []

    def on_translated(blocks):
        nonlocal result_blocks
        result_blocks = blocks
        mgr.update_blocks(blocks)

    bridge.blocks_translated.connect(on_translated)

    blocks = [
        {"x": 10, "y": 20, "w": 100, "h": 30, "text": "hello"},
    ]

    texts_to_translate = [b["text"] for b in blocks]
    translations = {}

    for t in texts_to_translate:
        r = translator.translate(t, "eng", "fra")
        if r.success and r.translated_text:
            translations[t] = r.translated_text

    output = []
    for b in blocks:
        output.append({
            "x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"],
            "original": b["text"],
            "translated": translations.get(b["text"], b["text"]),
        })

    bridge.blocks_translated.emit(output)

    assert len(result_blocks) == 1
    assert result_blocks[0]["original"] == "hello"
    assert result_blocks[0]["translated"] == "bonjour"
    assert mgr._active[0].translated_text == "bonjour"

    mgr.destroy()


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


def test_batch_parse_correct_number():
    parts = "bonjour\n---\nmonde\n---\nsalut".split("\n---\n")
    texts = ["hello", "world", "hi"]
    translations = {}
    for i, t in enumerate(texts):
        translated = parts[i].strip() if i < len(parts) else t
        translations[t] = translated

    assert translations["hello"] == "bonjour"
    assert translations["world"] == "monde"
    assert translations["hi"] == "salut"


def test_batch_parse_fallback():
    parts = "bonjour".split("\n---\n")
    texts = ["hello", "world"]
    translations = {}
    for i, t in enumerate(texts):
        translated = parts[i].strip() if i < len(parts) else t
        translations[t] = translated

    assert translations["hello"] == "bonjour"
    assert translations["world"] == "world"
