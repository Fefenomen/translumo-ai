import pytest
from ocr import text_significantly_different, normalize_text


class TestNormalize:
    def test_none(self):
        assert normalize_text(None) is None

    def test_strip(self):
        assert normalize_text("  hello  ") == "hello"

    def test_collapse_spaces(self):
        assert normalize_text("hello   world") == "hello world"

    def test_newlines(self):
        assert normalize_text("hello\nworld\n") == "hello world"

    def test_mixed_whitespace(self):
        assert normalize_text("hello\t world\r\nfoo") == "hello world foo"


class TestTextSignificantlyDifferent:
    def test_both_none(self):
        assert text_significantly_different(None, None) is False

    def test_one_none(self):
        assert text_significantly_different(None, "hello") is True
        assert text_significantly_different("hello", None) is True

    def test_identical(self):
        assert text_significantly_different("hello", "hello") is False
        assert text_significantly_different("こんにちは", "こんにちは") is False

    def test_ignore_whitespace(self):
        assert text_significantly_different("hello", " hello\n") is False

    def test_minor_change_below_threshold(self):
        assert text_significantly_different("hello", "hello!") is True

    def test_short_diff_above_threshold(self):
        assert text_significantly_different("abc", "abcd") is True

    def test_old_empty_new_not(self):
        assert text_significantly_different("", "hello") is True

    def test_old_not_empty_new_empty(self):
        assert text_significantly_different("hello", "") is False

    def test_identical_after_normalize(self):
        assert text_significantly_different("Hello  World", "Hello World") is False
        assert text_significantly_different("Line1\nLine2", "Line1 Line2") is False

    def test_concat_same_content(self):
        a = "体力|攻撃力"
        b = "体力 | 攻撃力"
        assert text_significantly_different(a, b) is False

    def test_different_content(self):
        assert text_significantly_different("hello", "world") is True
