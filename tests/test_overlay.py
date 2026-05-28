from PyQt5.QtCore import Qt
from overlay import TranslationWindow


def test_window_creation(qapp):
    w = TranslationWindow(text_color="#ffffff", bg_color="#1a1a1a", font_size=16)
    assert w.windowTitle() == "Translumo-AI"
    assert w.minimumWidth() == 300
    assert w.minimumHeight() == 100
    flags = w.windowFlags()
    assert flags & Qt.WindowStaysOnTopHint
    w.close()


def test_set_text(qapp):
    w = TranslationWindow()
    w.set_text("Hello translated world")
    assert w.text_edit.toPlainText() == "Hello translated world"
    w.close()


def test_clear_text(qapp):
    w = TranslationWindow()
    w.set_text("something")
    w.clear_text()
    assert w.text_edit.toPlainText() == ""
    w.close()


def test_show_hide(qapp):
    w = TranslationWindow()
    assert w.isVisible() is False
    w.show()
    assert w.isVisible() is True
    w.hide()
    assert w.isVisible() is False
    w.close()


def test_resize_persists(qapp):
    w = TranslationWindow()
    w.resize(600, 400)
    assert w.width() == 600
    assert w.height() == 400
    w.close()
