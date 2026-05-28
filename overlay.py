from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QFont


class BlockOverlay(QWidget):
    def __init__(self, bg_color="#1a1a1a", text_color="#ffffff", font_size=16, opacity=200):
        super().__init__(None)
        self.bg_color = QColor(bg_color)
        self.text_color = QColor(text_color)
        self.text_color.setAlpha(255)
        self.bg_color.setAlpha(opacity)
        self.font_size = font_size
        self.original_text = ""
        self.translated_text = ""

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            f"color: {text_color};"
            f"font-size: {font_size}px;"
            f"font-family: monospace;"
            f"background: transparent;"
            f"padding: 2px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def set_text(self, original: str, translated: str):
        self.original_text = original
        self.translated_text = translated
        self.label.setText(translated)
        self.label.adjustSize()
        min_w = min(self.label.width() + 8, 600)
        min_h = min(self.label.height() + 8, 400)
        self.setFixedSize(min_w, min_h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.bg_color)
        painter.setPen(QColor(self.text_color))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.end()
        super().paintEvent(event)


class OverlayManager:
    def __init__(self, bg_color="#1a1a1a", text_color="#ffffff", font_size=16, opacity=200):
        self.bg_color = bg_color
        self.text_color = text_color
        self.font_size = font_size
        self.opacity = opacity
        self._pool: list[BlockOverlay] = []
        self._active: list[BlockOverlay] = []
        self._region_origin = (0, 0)
        self._visible = False

    def set_region_origin(self, x: int, y: int):
        self._region_origin = (x, y)

    def _get_overlay(self) -> BlockOverlay:
        if self._pool:
            w = self._pool.pop()
            w.setVisible(True)
            return w
        return BlockOverlay(
            bg_color=self.bg_color,
            text_color=self.text_color,
            font_size=self.font_size,
            opacity=self.opacity,
        )

    def update_blocks(self, blocks: list[dict]):
        used_screens = set()
        matched = []

        for b in blocks:
            bx, by, bw, bh = b["x"], b["y"], b["w"], b["h"]
            ox, oy = self._region_origin
            screen_rect = QRect(ox + bx, oy + by, max(bw, 20), max(bh, 20))

            best = None
            best_dist = 100
            for i, existing in enumerate(self._active):
                if i in used_screens:
                    continue
                er = existing.geometry()
                cx1 = er.x() + er.width() // 2
                cy1 = er.y() + er.height() // 2
                cx2 = screen_rect.x() + screen_rect.width() // 2
                cy2 = screen_rect.y() + screen_rect.height() // 2
                dist = ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best = i

            if best is not None:
                w = self._active[best]
                used_screens.add(best)
            else:
                w = self._get_overlay()

            w.setGeometry(screen_rect)
            w.set_text(b.get("original", b["text"]), b.get("translated", b["text"]))
            if not self._visible:
                w.show()
            matched.append(w)

        # Return unmatched to pool
        remaining = []
        for i, w in enumerate(self._active):
            if i in used_screens:
                remaining.append(w)
            else:
                w.setVisible(False)
                self._pool.append(w)

        self._active = matched

    def show_all(self):
        self._visible = True
        for w in self._active:
            w.show()

    def hide_all(self):
        self._visible = False
        for w in self._active:
            w.setVisible(False)

    def clear(self):
        self.hide_all()
        for w in self._active:
            self._pool.append(w)
        self._active = []

    def destroy(self):
        self.clear()
        for w in self._pool:
            w.deleteLater()
        self._pool = []
