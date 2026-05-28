import sys
import time
import threading

from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QTimer

import os
from config import load_config, save_config, get_api_key
from capture import select_region, capture_region_np
from ocr import ocr_image, text_significantly_different
from translators import get_translator, TRANSLATOR_MAP
from overlay import TranslationOverlay
from settings_dialog import SettingsDialog


class TranslumoAI:
    def __init__(self):
        self.app = QApplication(sys.argv + ["-platform", "wayland"])
        self.app.setApplicationName("Translumo-AI")
        self.app.setQuitOnLastWindowClosed(False)

        self.cfg = load_config()
        self.overlay = None
        self.translator = None
        self.running = False
        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self.capture_and_translate)

        self.last_text = None
        self.last_translation_time = 0
        self.min_interval_between_api = 1.0

        self._init_translator()
        self._init_tray()
        self._select_region_startup()

    def _init_translator(self):
        provider = self.cfg.get("provider", "openai")
        api_key = get_api_key(provider)
        self.translator = get_translator(
            provider,
            api_key=api_key,
            ollama_url=self.cfg.get("ollama_url", "http://localhost:11434"),
            ollama_model=self.cfg.get("ollama_model", "llama3"),
        )

    def _init_tray(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon_path):
            self.tray = QSystemTrayIcon(QIcon(icon_path))
        else:
            self.tray = QSystemTrayIcon()
        self.tray.setToolTip("Translumo-AI")

        menu = QMenu()

        toggle_action = QAction("Start/Stop Translation", menu)
        toggle_action.triggered.connect(self.toggle_translation)
        menu.addAction(toggle_action)

        select_region_action = QAction("Select Region", menu)
        select_region_action.triggered.connect(self.select_new_region)
        menu.addAction(select_region_action)

        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()
        self.tray.showMessage("Translumo-AI", "Select a region to start translation.", QSystemTrayIcon.Information, 3000)

    def _select_region_startup(self):
        if self.cfg.get("capture_region"):
            self._setup_overlay(self.cfg["capture_region"])
            self.start_translation()

    def select_new_region(self):
        if self.running:
            self.stop_translation()
        geometry = select_region()
        if geometry:
            self.cfg["capture_region"] = geometry
            save_config(self.cfg)
            self._setup_overlay(geometry)
            self.start_translation()
        else:
            self.tray.showMessage(
                "Translumo-AI", "Region selection cancelled or failed.",
                QSystemTrayIcon.Warning, 3000
            )

    def _setup_overlay(self, geometry):
        if self.overlay:
            self.overlay.hide_overlay()
            self.overlay.deleteLater()
        self.overlay = TranslationOverlay(
            geometry=geometry,
            bg_color=self.cfg.get("overlay_bg_color", "#1a1a1a"),
            text_color=self.cfg.get("overlay_text_color", "#ffffff"),
            font_size=self.cfg.get("overlay_font_size", 16),
            opacity=self.cfg.get("overlay_opacity", 180),
        )

    def toggle_translation(self):
        if self.running:
            self.stop_translation()
        else:
            self.start_translation()

    def start_translation(self):
        if not self.overlay:
            self.tray.showMessage(
                "Translumo-AI", "Please select a region first.",
                QSystemTrayIcon.Warning, 3000
            )
            return
        self.running = True
        self.last_text = None
        interval = self.cfg.get("capture_interval_ms", 800)
        self.capture_timer.start(interval)
        self.tray.showMessage(
            "Translumo-AI", f"Translation started (every {interval}ms).",
            QSystemTrayIcon.Information, 2000
        )

    def stop_translation(self):
        self.running = False
        self.capture_timer.stop()
        if self.overlay:
            self.overlay.hide_overlay()
        self.tray.showMessage(
            "Translumo-AI", "Translation stopped.",
            QSystemTrayIcon.Information, 2000
        )

    def capture_and_translate(self):
        geometry = self.cfg.get("capture_region")
        if not geometry:
            return

        arr = capture_region_np(geometry)
        if arr is None:
            return

        ocr_lang = self.cfg.get("ocr_lang", "jpn+eng")
        text = ocr_image(arr, lang=ocr_lang)
        if not text:
            return

        if not text_significantly_different(self.last_text, text):
            return

        self.last_text = text
        self._translate_async(text)

    def _translate_async(self, text):
        def do_translate():
            now = time.time()
            if now - self.last_translation_time < self.min_interval_between_api:
                return
            self.last_translation_time = now

            source = self.cfg.get("source_lang", "jpn")
            target = self.cfg.get("target_lang", "fra")

            result = self.translator.translate(text, source, target)
            if result.success and result.translated_text:
                self._update_overlay(text, result.translated_text)

        thread = threading.Thread(target=do_translate, daemon=True)
        thread.start()

    def _update_overlay(self, original, translated):
        if self.overlay:
            self.overlay.update_text(original, translated)
            self.overlay.show_overlay()

    def open_settings(self):
        dialog = SettingsDialog()
        if dialog.exec_():
            self.cfg = load_config()
            self._init_translator()
            if self.overlay:
                geometry = self.cfg.get("capture_region")
                if geometry:
                    self.overlay.set_geometry_from_tuple(geometry)

    def quit(self):
        self.stop_translation()
        if self.overlay:
            self.overlay.hide_overlay()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    app = TranslumoAI()
    app.run()
