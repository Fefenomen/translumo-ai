from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPen


class TranslationOverlay(QWidget):
    def __init__(self, geometry=None, bg_color="#1a1a1a", text_color="#ffffff",
                 font_size=16, opacity=180):
        super().__init__(None)
        self.bg_color = QColor(bg_color)
        self.text_color = QColor(text_color)
        self.bg_color.setAlpha(opacity)
        self.font_size = font_size
        self.translated_text = ""
        self.original_text = ""
        self.is_visible = False

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
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
        layout.addWidget(self.label)
        layout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(layout)

        if geometry:
            x, y, w, h = geometry
            self.setGeometry(x, y, w, h)

    def update_text(self, original: str, translated: str):
        self.original_text = original
        self.translated_text = translated
        self.label.setText(translated)
        self.show()
        self.raise_()

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
        self.is_visible = True
        self.show()
        self.raise_()

    def hide_overlay(self):
        self.is_visible = False
        self.hide()
