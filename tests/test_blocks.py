import numpy as np
from PIL import Image, ImageDraw
from ocr import ocr_image_blocks, ocr_image
from .conftest import create_test_image


def test_ocr_blocks_detects_text():
    arr = create_test_image("Hello World")
    blocks = ocr_image_blocks(arr, lang="eng")
    assert len(blocks) >= 1, "Should detect at least one block"
    merged = " ".join(b["text"] for b in blocks)
    assert "Hello" in merged or "World" in merged


def test_ocr_blocks_return_geometry():
    arr = create_test_image("Test")
    blocks = ocr_image_blocks(arr, lang="eng")
    assert len(blocks) >= 1
    b = blocks[0]
    for key in ("x", "y", "w", "h", "text"):
        assert key in b, f"Missing key: {key}"
    assert b["w"] > 0
    assert b["h"] > 0


def test_ocr_blocks_empty_on_blank():
    arr = np.zeros((100, 100, 3), dtype=np.uint8) + 255
    blocks = ocr_image_blocks(arr, lang="eng")
    assert blocks == [], "Should return empty on blank image"


def test_ocr_blocks_multiple_lines():
    img = Image.new("RGB", (600, 200), "white")
    draw = ImageDraw.Draw(img)
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 24)
    except (OSError, ImportError):
        font = ImageFont.load_default()
    draw.text((20, 20), "Line one", fill="black", font=font)
    draw.text((20, 80), "Line two", fill="black", font=font)
    arr = np.array(img)
    blocks = ocr_image_blocks(arr, lang="eng")
    assert len(blocks) >= 1, "Should detect at least one block"
    merged = " ".join(b["text"] for b in blocks)
    assert "Line" in merged


def test_ocr_blocks_filters_short_text():
    arr = create_test_image("A")
    blocks = ocr_image_blocks(arr, lang="eng")
    for b in blocks:
        assert len(b["text"]) >= 2, "Should filter single-char text"
