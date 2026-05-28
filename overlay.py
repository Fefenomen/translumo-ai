from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout
from PyQt5.QtCore import Qt


class TranslationWindow(QWidget):
    def __init__(self, text_color="#ffffff", bg_color="#1a1a1a", font_size=16):
        super().__init__(None)
        self.setWindowTitle("Translumo-AI")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.Window
        )
        self.setMinimumSize(300, 100)
        self.resize(400, 300)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(
            f"background-color: {bg_color};"
            f"color: {text_color};"
            f"font-size: {font_size}px;"
            f"font-family: monospace;"
            f"padding: 8px;"
            f"border: none;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def set_text(self, translated: str):
        self.text_edit.setPlainText(translated)

    def clear_text(self):
        self.text_edit.clear()
