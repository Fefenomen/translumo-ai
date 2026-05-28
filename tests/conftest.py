import sys

import numpy as np
import pytest
from PIL import Image, ImageDraw
from PyQt5.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv + ["-platform", "wayland"])
    return app


def create_test_image(text: str, width=600, height=100):
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 28)
    except (OSError, ImportError):
        font = ImageFont.load_default()
    draw.text((20, 30), text, fill="black", font=font)
    return np.array(img)
