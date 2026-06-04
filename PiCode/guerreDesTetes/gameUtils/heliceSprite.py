import cv2
import os 
import numpy as np
from pathlib import Path
from typing import List
from guerreDesTetes.overlay import overlay_png_opacite, overlay_png_png


def createHeliceSprite(sprite: np.ndarray, path="guerreDesTetes/helicopter/") -> List[np.ndarray]:
    files = [f for f in os.listdir(path) if f.startswith("test") and f.lower().endswith((".png", ".jpg", ".jpeg"))]
    HELICE: List[np.ndarray] = []

    for f in files:
        img = cv2.imread(os.path.join(path, f), cv2.IMREAD_UNCHANGED)
        if img is None:
            print("caca")
        HELICE.append(img)


    if sprite is None:
        raise ValueError("sprite is None")

    sprites: List[np.ndarray] = []

    for heli in HELICE:
        result = np.zeros((heli.shape[0], heli.shape[1], 4), dtype=np.uint8)
        
        cx_result = result.shape[1] // 2
        cy_result = result.shape[0] // 2
        result = overlay_png_png(result, sprite, cx_result, cy_result)
        
        result = overlay_png_png(result, heli, cx_result, cy_result)
        
        sprites.append(result)
    return sprites

if __name__ == "__main__":

    selfies_dir = Path(__file__).resolve().parents[1] / "selfies"

    sprite_img = cv2.imread(str(selfies_dir / "sprite_000.png"), cv2.IMREAD_UNCHANGED)

    sprites = createHeliceSprite(sprite_img)

    for i, s in enumerate(sprites):
        cv2.imshow(f"helice_{i+1}", s)
    cv2.waitKey(0)
    cv2.destroyAllWindows()