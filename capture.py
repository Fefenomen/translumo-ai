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


def spectable_capture(geometry: Optional[Geometry] = None) -> Optional[Image.Image]:
    tmp = tempfile.mktemp(suffix=".png")
    try:
        cmd = ["spectacle", "-b", "-n", "-o", tmp]
        if geometry:
            x, y, w, h = geometry
            cmd = ["spectacle", "-b", "-n", "-r", "-o", tmp]
        result = subprocess.run(cmd, capture_output=True, timeout=15)
        if result.returncode != 0:
            return None
        if not os.path.exists(tmp) or os.path.getsize(tmp) == 0:
            return None
        img = Image.open(tmp)
        if geometry:
            x, y, w, h = geometry
            img = img.crop((x, y, x + w, y + h))
        return img
    except Exception:
        return None
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def spectacle_capture_full() -> Optional[Image.Image]:
    return spectable_capture()


def capture_region_np(geometry: Geometry) -> Optional[np.ndarray]:
    x, y, w, h = geometry
    img = spectable_capture()
    if img is None:
        return None
    x = max(0, x)
    y = max(0, y)
    w = min(w, img.width - x)
    h = min(h, img.height - y)
    if w <= 0 or h <= 0:
        return None
    arr = np.array(img.convert("RGB"))
    return arr[y:y+h, x:x+w].copy()


def capture_monitor_np() -> Optional[np.ndarray]:
    tmp = tempfile.mktemp(suffix=".png")
    try:
        subprocess.run(
            ["spectacle", "-m", "-b", "-n", "-o", tmp],
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
