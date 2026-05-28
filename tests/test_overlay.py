from PyQt5.QtCore import Qt
from overlay import BlockOverlay, OverlayManager


def test_block_overlay_creation(qapp):
    o = BlockOverlay(bg_color="#1a1a1a", text_color="#ffffff", font_size=16, opacity=200)
    assert o.translated_text == ""
    assert o.original_text == ""
    flags = o.windowFlags()
    assert flags & Qt.FramelessWindowHint
    assert flags & Qt.WindowStaysOnTopHint
    assert flags & Qt.WindowDoesNotAcceptFocus
    assert o.testAttribute(Qt.WA_TranslucentBackground)
    assert o.testAttribute(Qt.WA_ShowWithoutActivating)
    assert o.testAttribute(Qt.WA_TransparentForMouseEvents)
    o.deleteLater()


def test_block_overlay_set_text(qapp):
    o = BlockOverlay()
    o.set_text("original", "translated")
    assert o.original_text == "original"
    assert o.translated_text == "translated"
    assert o.label.text() == "translated"
    o.deleteLater()


def test_block_overlay_auto_size(qapp):
    o = BlockOverlay(font_size=16)
    o.set_text("test", "translated text here")
    assert o.width() > 0
    assert o.height() > 0
    o.deleteLater()


class TestOverlayManager:
    def test_initial_state(self, qapp):
        mgr = OverlayManager()
        assert mgr._pool == []
        assert mgr._active == []
        mgr.destroy()

    def test_update_blocks_creates_overlays(self, qapp):
        mgr = OverlayManager()
        blocks = [
            {"x": 100, "y": 200, "w": 300, "h": 50, "text": "hello",
             "original": "hello", "translated": "bonjour"},
        ]
        mgr.update_blocks(blocks)
        assert len(mgr._active) == 1
        w = mgr._active[0]
        assert w.original_text == "hello"
        assert w.translated_text == "bonjour"
        mgr.destroy()

    def test_update_blocks_recycles(self, qapp):
        mgr = OverlayManager()
        blocks = [
            {"x": 0, "y": 0, "w": 100, "h": 30, "text": "a",
             "original": "a", "translated": "a"},
            {"x": 0, "y": 100, "w": 100, "h": 30, "text": "b",
             "original": "b", "translated": "b"},
        ]
        mgr.update_blocks(blocks)
        ids = [id(w) for w in mgr._active]
        assert len(mgr._active) == 2

        # Same positions → reuse widgets
        mgr.update_blocks(blocks)
        ids2 = [id(w) for w in mgr._active]
        assert ids == ids2, "Should reuse widgets for same positions"
        mgr.destroy()

    def test_pool_recycle(self, qapp):
        mgr = OverlayManager()
        blocks = [{"x": 0, "y": 0, "w": 100, "h": 30, "text": "a",
                    "original": "a", "translated": "a"}]
        mgr.update_blocks(blocks)
        assert len(mgr._active) == 1
        assert len(mgr._pool) == 0

        # New blocks at different position → old one goes to pool
        blocks2 = [{"x": 500, "y": 500, "w": 100, "h": 30, "text": "b",
                     "original": "b", "translated": "b"}]
        mgr.update_blocks(blocks2)
        assert len(mgr._pool) == 1
        mgr.destroy()

    def test_region_origin_offset(self, qapp):
        mgr = OverlayManager()
        mgr.set_region_origin(100, 200)
        blocks = [{"x": 10, "y": 20, "w": 50, "h": 30, "original": "t", "translated": "t"}]
        mgr.update_blocks(blocks)
        w = mgr._active[0]
        assert w.x() == 110
        assert w.y() == 220
        mgr.destroy()

    def test_show_hide(self, qapp):
        mgr = OverlayManager()
        blocks = [{"x": 0, "y": 0, "w": 100, "h": 30, "original": "t", "translated": "t"}]
        mgr.update_blocks(blocks)
        mgr.show_all()
        assert mgr._visible is True
        assert mgr._active[0].isVisible()
        mgr.hide_all()
        assert mgr._visible is False
        assert mgr._active[0].isVisible() is False
        mgr.destroy()

    def test_clear_returns_to_pool(self, qapp):
        mgr = OverlayManager()
        blocks = [{"x": 0, "y": 0, "w": 100, "h": 30, "original": "t", "translated": "t"}]
        mgr.update_blocks(blocks)
        mgr.clear()
        assert mgr._active == []
        assert len(mgr._pool) == 1
        mgr.destroy()
