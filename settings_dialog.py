from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QSpinBox, QGroupBox, QFormLayout,
    QTabWidget, QWidget, QMessageBox, QSlider
)
from PyQt5.QtCore import Qt
from config import load_config, save_config

LANGUAGES = {
    "eng": "English",
    "fra": "French",
    "jpn": "Japanese",
    "kor": "Korean",
    "chi_sim": "Chinese (Simplified)",
    "rus": "Russian",
    "deu": "German",
    "spa": "Spanish",
    "ita": "Italian",
    "por": "Portuguese",
    "ara": "Arabic",
    "nld": "Dutch",
    "pol": "Polish",
    "swe": "Swedish",
    "tur": "Turkish",
    "vie": "Vietnamese",
    "tha": "Thai",
    "hin": "Hindi",
}

PROVIDERS = ["openai", "anthropic", "mistral", "gemini", "ollama"]


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = load_config()
        self.setWindowTitle("Translumo-AI Settings")
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        general_tab = self._build_general_tab()
        api_tab = self._build_api_tab()
        overlay_tab = self._build_overlay_tab()

        tabs.addTab(general_tab, "General")
        tabs.addTab(api_tab, "API Keys")
        tabs.addTab(overlay_tab, "Overlay")

        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _build_general_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        self.source_lang = QComboBox()
        self.target_lang = QComboBox()
        self.ocr_lang = QComboBox()
        for code, name in sorted(LANGUAGES.items(), key=lambda x: x[1]):
            self.source_lang.addItem(f"{name} ({code})", code)
            self.target_lang.addItem(f"{name} ({code})", code)
            self.ocr_lang.addItem(f"{name} ({code})", code)

        self.set_combo(self.source_lang, self.cfg.get("source_lang", "jpn"))
        self.set_combo(self.target_lang, self.cfg.get("target_lang", "fra"))
        self.set_combo(self.ocr_lang, self.cfg.get("ocr_lang", "jpn+eng").split("+")[0])

        self.provider = QComboBox()
        for p in PROVIDERS:
            self.provider.addItem(p.capitalize(), p)
        self.set_combo(self.provider, self.cfg.get("provider", "openai"))

        self.interval = QSpinBox()
        self.interval.setRange(200, 5000)
        self.interval.setSingleStep(100)
        self.interval.setSuffix(" ms")
        self.interval.setValue(self.cfg.get("capture_interval_ms", 800))

        self.ollama_url = QLineEdit(self.cfg.get("ollama_url", "http://localhost:11434"))
        self.ollama_model = QLineEdit(self.cfg.get("ollama_model", "llama3"))

        form.addRow("Source Language:", self.source_lang)
        form.addRow("Target Language:", self.target_lang)
        form.addRow("OCR Language:", self.ocr_lang)
        form.addRow("AI Provider:", self.provider)
        form.addRow("Capture Interval:", self.interval)
        form.addRow("Ollama URL:", self.ollama_url)
        form.addRow("Ollama Model:", self.ollama_model)

        return tab

    def _build_api_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        self.api_keys = {}
        for provider in PROVIDERS:
            key = self.cfg.get("api_keys", {}).get(provider, "")
            edit = QLineEdit(key)
            edit.setEchoMode(QLineEdit.Password)
            edit.setPlaceholderText(f"Enter {provider.capitalize()} API key")
            self.api_keys[provider] = edit
            form.addRow(f"{provider.capitalize()}:", edit)

        return tab

    def _build_overlay_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        self.font_size.setValue(self.cfg.get("overlay_font_size", 16))

        self.opacity = QSlider(Qt.Horizontal)
        self.opacity.setRange(30, 255)
        self.opacity.setValue(self.cfg.get("overlay_opacity", 180))
        self.opacity_label = QLabel(str(self.opacity.value()))
        self.opacity.valueChanged.connect(lambda v: self.opacity_label.setText(str(v)))

        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.opacity)
        opacity_layout.addWidget(self.opacity_label)

        self.bg_color = QLineEdit(self.cfg.get("overlay_bg_color", "#1a1a1a"))
        self.text_color = QLineEdit(self.cfg.get("overlay_text_color", "#ffffff"))

        form.addRow("Font Size:", self.font_size)
        form.addRow("Opacity:", opacity_layout)
        form.addRow("Background Color:", self.bg_color)
        form.addRow("Text Color:", self.text_color)

        return tab

    def set_combo(self, combo, value):
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def save_settings(self):
        ocr_code = self.ocr_lang.currentData()
        ocr_lang = f"{ocr_code}+eng" if ocr_code != "eng" else "eng"

        self.cfg["source_lang"] = self.source_lang.currentData()
        self.cfg["target_lang"] = self.target_lang.currentData()
        self.cfg["ocr_lang"] = ocr_lang
        self.cfg["provider"] = self.provider.currentData()
        self.cfg["capture_interval_ms"] = self.interval.value()
        self.cfg["ollama_url"] = self.ollama_url.text().strip()
        self.cfg["ollama_model"] = self.ollama_model.text().strip()

        for provider, edit in self.api_keys.items():
            val = edit.text().strip()
            if val:
                self.cfg["api_keys"][provider] = val

        self.cfg["overlay_font_size"] = self.font_size.value()
        self.cfg["overlay_opacity"] = self.opacity.value()
        self.cfg["overlay_bg_color"] = self.bg_color.text().strip()
        self.cfg["overlay_text_color"] = self.text_color.text().strip()

        save_config(self.cfg)
        QMessageBox.information(self, "Saved", "Settings saved successfully.")
        self.accept()
