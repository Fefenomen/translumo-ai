import os
import re
import subprocess
import tempfile
import time
from typing import Optional, Tuple

import numpy as np
from PIL import Image

Geometry = Tuple[int, int, int, int]  # x, y, width, height


def parse_slurp_geometry(text: str) -> Optional[Geometry]:
    m = re.match(r"(\d+),(\d+)\s+(\d+)x(\d+)", text.strip())
    if m:
        return (int(m[1]), int(m[2]), int(m[3]), int(m[4]))
    return None


def select_region() -> Optional[Geometry]:
    try:
        result = subprocess.run(
            ["slurp", "-d"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return parse_slurp_geometry(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def select_monitor() -> Optional[Geometry]:
    try:
        result = subprocess.run(
            ["slurp", "-or"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return parse_slurp_geometry(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def capture_full_screen_np() -> Optional[np.ndarray]:
    tmp = tempfile.mktemp(suffix=".png")
    try:
        subprocess.run(
            ["spectacle", "-b", "-n", "-o", tmp],
            capture_output=True, timeout=15
        )
        if not os.path.exists(tmp) or os.path.getsize(tmp) == 0:
            return None
        img = Image.open(tmp)
        return np.array(img.convert("RGB"))
    except Exception:
        return None
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def capture_region_np(geometry: Geometry) -> Optional[np.ndarray]:
    x, y, w, h = geometry
    full = capture_full_screen_np()
    if full is None:
        return None
    fh, fw = full.shape[:2]
    x = max(0, min(x, fw - 1))
    y = max(0, min(y, fh - 1))
    w = min(w, fw - x)
    h = min(h, fh - y)
    if w <= 0 or h <= 0:
        return None
    return full[y:y+h, x:x+w].copy()
