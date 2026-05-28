from typing import Optional
import cv2
import numpy as np
import pytesseract


def preprocess_image(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    denoised = cv2.medianBlur(thresh, 1)
    return denoised


def ocr_image(img: np.ndarray, lang: str = "jpn+eng") -> Optional[str]:
    processed = preprocess_image(img)
    try:
        text = pytesseract.image_to_string(processed, lang=lang, config="--psm 6")
        text = text.strip()
        return text if text else None
    except Exception:
        return None


def text_significantly_different(old: Optional[str], new: Optional[str]) -> bool:
    if old is None and new is None:
        return False
    if old is None or new is None:
        return True
    if old == new:
        return False
    if len(old) > 0 and len(new) == 0:
        return False
    max_len = max(len(old), len(new))
    if max_len == 0:
        return False
    diffs = sum(1 for a, b in zip(old, new) if a != b)
    diffs += abs(len(old) - len(new))
    diff_ratio = diffs / max_len
    return diff_ratio > 0.15
