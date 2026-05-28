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


def ocr_image_blocks(img: np.ndarray, lang: str = "jpn+eng") -> list[dict]:
    processed = preprocess_image(img)
    try:
        data = pytesseract.image_to_data(
            processed, lang=lang, output_type=pytesseract.Output.DICT, config="--psm 6"
        )
        words_by_block: dict[int, list[dict]] = {}
        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            conf = data["conf"][i]
            if not text or conf == "-1" or int(conf) < 20:
                continue
            bn = data["block_num"][i]
            if bn not in words_by_block:
                words_by_block[bn] = []
            words_by_block[bn].append({
                "x": data["left"][i],
                "y": data["top"][i],
                "w": data["width"][i],
                "h": data["height"][i],
                "text": text,
            })

        blocks = []
        for bn, words in words_by_block.items():
            if not words:
                continue
            min_x = min(w["x"] for w in words)
            min_y = min(w["y"] for w in words)
            max_x = max(w["x"] + w["w"] for w in words)
            max_y = max(w["y"] + w["h"] for w in words)
            text = " ".join(w["text"] for w in words)
            blocks.append({
                "x": min_x, "y": min_y,
                "w": max_x - min_x, "h": max_y - min_y,
                "text": text,
            })

        merged = []
        for b in sorted(blocks, key=lambda b: (b["y"], b["x"])):
            if not merged:
                merged.append(b)
                continue
            last = merged[-1]
            vert_gap = b["y"] - (last["y"] + last["h"])
            h_overlap = min(b["x"] + b["w"], last["x"] + last["w"]) - max(b["x"], last["x"])
            if vert_gap < 15 and h_overlap > -50:
                last["x"] = min(last["x"], b["x"])
                last["y"] = min(last["y"], b["y"])
                last["w"] = max(last["x"] + last["w"], b["x"] + b["w"]) - last["x"]
                last["h"] = max(last["y"] + last["h"], b["y"] + b["h"]) - last["y"]
                last["text"] = last["text"] + " " + b["text"]
            else:
                merged.append(b)

        result = [
            {"x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"], "text": b["text"].strip()}
            for b in merged if len(b["text"].strip()) >= 2
        ]
        return result
    except Exception:
        return []


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
