import sys
import time
import threading

from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal, pyqtSlot, QThread

import os
from config import load_config, save_config, get_api_key
from capture import select_region, capture_region_np
from ocr import ocr_image, text_significantly_different
from translators import get_translator
from overlay import TranslationOverlay
from settings_dialog import SettingsDialog


class CaptureWorker(QObject):
    text_ready = pyqtSignal(str)
    capture_failed = pyqtSignal()
    sig_start = pyqtSignal()
    sig_stop = pyqtSignal()
    sig_set_interval = pyqtSignal(int)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.timer = QTimer()
        self.timer.timeout.connect(self._capture)
        self.sig_start.connect(self.timer.start, Qt.QueuedConnection)
        self.sig_stop.connect(self.timer.stop, Qt.QueuedConnection)
        self.sig_set_interval.connect(self._set_interval_slot, Qt.QueuedConnection)

    @pyqtSlot(int)
    def _set_interval_slot(self, ms):
        was_running = self.timer.isActive()
        if was_running:
            self.timer.stop()
        self.timer.setInterval(ms)
        if was_running:
            self.timer.start()

    def _capture(self):
        geometry = self.cfg.get("capture_region")
        if not geometry:
            return
        arr = capture_region_np(geometry)
        if arr is None:
            self.capture_failed.emit()
            return
        ocr_lang = self.cfg.get("ocr_lang", "jpn+eng")
        text = ocr_image(arr, lang=ocr_lang)
        if text:
            self.text_ready.emit(text)


class TranslumoAI:
    def __init__(self):
        self.app = QApplication(sys.argv + ["-platform", "wayland"])
        self.app.setApplicationName("Translumo-AI")
        self.app.setQuitOnLastWindowClosed(False)

        self.cfg = load_config()
        self.overlay = None
        self.translator = None
        self.running = False
        self.last_text = None
        self.last_translation_time = 0
        self.min_interval_between_api = 1.0
        self.translation_cache = {}
        self.cache_max_size = 100
        self.debounce_stable_count = 0
        self.debounce_threshold = 3

        self._init_translator()
        self._init_worker()
        self._init_tray()
        self._select_region_startup()

    def _init_translator(self):
        provider = self.cfg.get("provider", "ollama")
        api_key = get_api_key(provider)
        self.translator = get_translator(
            provider,
            api_key=api_key,
            ollama_url=self.cfg.get("ollama_url", "http://localhost:11434"),
            ollama_model=self.cfg.get("ollama_model", "aya:8b"),
        )

    def _init_worker(self):
        self.worker = CaptureWorker(self.cfg)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker.text_ready.connect(self._on_text_ready)
        self.worker.capture_failed.connect(self._on_capture_failed)
        self.worker_thread.start()

    def _on_capture_failed(self):
        self._tray_msg("Capture failed - check spectacle permissions", 2000)

    def _on_text_ready(self, text):
        if text == self.last_text:
            self.debounce_stable_count += 1
            if self.debounce_stable_count >= self.debounce_threshold:
                self._translate_async(text)
            return
        if not text_significantly_different(self.last_text, text):
            return
        self.last_text = text
        self.debounce_stable_count = 1

    def _translate_async(self, text):
        def do_translate():
            now = time.time()
            if now - self.last_translation_time < self.min_interval_between_api:
                return

            cached = self.translation_cache.get(text)
            if cached is not None:
                self._update_overlay(text, cached)
                return

            self.last_translation_time = now

            source = self.cfg.get("source_lang", "jpn")
            target = self.cfg.get("target_lang", "fra")

            result = self.translator.translate(text, source, target)
            if result.success and result.translated_text:
                self.translation_cache[text] = result.translated_text
                if len(self.translation_cache) > self.cache_max_size:
                    self.translation_cache.pop(next(iter(self.translation_cache)))
                self._update_overlay(text, result.translated_text)
            else:
                err = result.error or "Unknown error"
                self._tray_msg(f"Translation failed: {err[:60]}", 3000)

        thread = threading.Thread(target=do_translate, daemon=True)
        thread.start()

    def _update_overlay(self, original, translated):
        if self.overlay:
            self.overlay.update_text(original, translated)
            self.overlay.show_overlay()

    def _tray_msg(self, msg, duration=2000):
        try:
            self.tray.showMessage("Translumo-AI", msg, QSystemTrayIcon.Information, duration)
        except Exception:
            pass

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
        self._tray_msg("Select a region to start translation.", 3000)

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
            self._tray_msg("Region selection cancelled.", 3000)

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
            self._tray_msg("Please select a region first.", 3000)
            return
        self.running = True
        self.last_text = None
        interval = self.cfg.get("capture_interval_ms", 800)
        self.worker.sig_set_interval.emit(interval)
        self.worker.sig_start.emit()
        provider = self.cfg.get("provider", "ollama")
        model = self.cfg.get("ollama_model", "aya:8b") if provider == "ollama" else ""
        label = f"{provider}{f' ({model})' if model else ''}"
        self.tray.setToolTip(f"Translumo-AI — {label}")
        self._tray_msg(f"Translation started ({label}, every {interval}ms).", 2000)

    def stop_translation(self):
        self.running = False
        self.worker.sig_stop.emit()
        if self.overlay:
            self.overlay.hide_overlay()
        self._tray_msg("Translation stopped.", 2000)

    def open_settings(self):
        was_running = self.running
        if was_running:
            self.stop_translation()
        dialog = SettingsDialog()
        if dialog.exec_():
            self.cfg = load_config()
            self._init_translator()
            if self.overlay:
                geometry = self.cfg.get("capture_region")
                if geometry:
                    self.overlay.set_geometry_from_tuple(geometry)
                if was_running:
                    self.start_translation()

    def quit(self):
        self.stop_translation()
        self.worker_thread.quit()
        self.worker_thread.wait()
        if self.overlay:
            self.overlay.hide_overlay()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    app = TranslumoAI()
    app.run()
