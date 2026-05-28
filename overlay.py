from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor


class TranslationOverlay(QWidget):
    def __init__(self, geometry=None, bg_color="#1a1a1a", text_color="#ffffff",
                 font_size=16, opacity=180):
        super().__init__(None)
        self.bg_color = QColor(bg_color)
        self.text_color = QColor(text_color)
        self.bg_color.setAlpha(opacity)
        self.translated_text = ""
        self.original_text = ""
        self._active = False
        self._indicator_color = QColor("#ff4444")

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
            | Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            f"color: {text_color};"
            f"font-size: {font_size}px;"
            f"font-family: monospace;"
            f"background: transparent;"
            f"padding: 8px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 4)
        layout.setSpacing(4)
        self.indicator = QLabel(self)
        self.indicator.setFixedHeight(3)
        layout.addWidget(self.indicator)
        layout.addWidget(self.label)
        self.setLayout(layout)

        if geometry:
            x, y, w, h = geometry
            self.setGeometry(x, y, w, h)

    def set_active(self, active: bool):
        self._active = active
        self._indicator_color = QColor("#44ff44") if active else QColor("#ff4444")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.bg_color)
        indicator_rect = self.rect().adjusted(4, 4, -4, -8)
        indicator_rect.setHeight(3)
        painter.fillRect(indicator_rect, self._indicator_color)
        painter.end()
        super().paintEvent(event)

    def update_text(self, original: str, translated: str):
        self.original_text = original
        self.translated_text = translated
        self.label.setText(translated)

    def set_geometry_from_tuple(self, geometry):
        if geometry:
            x, y, w, h = geometry
            self.setGeometry(x, y, w, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.bg_color)
        painter.end()
        super().paintEvent(event)

    def show_overlay(self):
        self.setVisible(True)

    def hide_overlay(self):
        self.setVisible(False)
