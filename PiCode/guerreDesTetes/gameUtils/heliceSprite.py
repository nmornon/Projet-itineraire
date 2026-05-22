import cv2
import os 
import numpy as np
from pathlib import Path
from typing import List
from guerreDesTetes.overlay import overlay_png_opacite

HELICE_DIR = Path(__file__).resolve().parents[1] / "helicopter"
HELICE: List[np.ndarray] = []
for i in range(1, 5):
    p = HELICE_DIR / f"test{i}.png"
    img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    HELICE.append(img)

def createHeliceSprite(sprite: np.ndarray) -> List[np.ndarray]:
    if sprite is None:
        raise ValueError("sprite is None")

    sprites: List[np.ndarray] = []

    for heli in HELICE:
        base = heli.copy()
        cx = heli.shape[1] // 2
        cy = heli.shape[0] // 2
        img = overlay_png_opacite(base, sprite, cx, cy)
        img2 = overlay_png_opacite(img.copy(), heli, cx, cy)
        sprites.append(img2)
    return sprites

if __name__ == "__main__":

    selfies_dir = Path(__file__).resolve().parents[1] / "selfies"

    sprite_img = cv2.imread(str(selfies_dir / "sprite_000.png"), cv2.IMREAD_UNCHANGED)

    sprites = createHeliceSprite(sprite_img)

    for i, s in enumerate(sprites):
        cv2.imshow(f"helice_{i+1}", s)
    cv2.waitKey(0)
    cv2.destroyAllWindows()