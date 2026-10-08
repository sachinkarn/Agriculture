"""Estimate how much of the leaf is affected, from the photo itself.

Method: inside the leaf-like pixels (coloured, not white/grey background) count the share
that is NOT green (brown, yellow, black lesions). It is a simple image-processing estimate,
not a trained model, and it is fooled by brown soil or a brown hand in the frame.
"""
import numpy as np
from PIL import Image

# PIL HSV channels are 0..255. Green hues are roughly 60..170 degrees.
_GREEN_LO, _GREEN_HI = int(60 / 360 * 255), int(170 / 360 * 255)


def lesion_percent(image: Image.Image) -> float:
    img = image.convert("RGB")
    img.thumbnail((256, 256))
    w, h = img.size
    # Centre crop (80%) so edge background matters less.
    dx, dy = int(w * 0.1), int(h * 0.1)
    img = img.crop((dx, dy, w - dx, h - dy))
    hsv = np.asarray(img.convert("HSV"))
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    leaf = (sat > 50) & (val > 40)
    if leaf.sum() < 50:                      # nothing leaf-like in the frame
        return 0.0
    green = (hue >= _GREEN_LO) & (hue <= _GREEN_HI)
    return float(100.0 * (leaf & ~green).sum() / leaf.sum())


def severity_label(pct: float) -> str:
    if pct < 8:
        return "Low"
    if pct < 20:
        return "Medium"
    return "High"
