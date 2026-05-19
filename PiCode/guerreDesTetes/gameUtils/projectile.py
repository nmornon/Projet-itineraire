import time
import cv2
import numpy as np

from pathlib import Path
from typing import List, Optional, Tuple
from overlay import overlay_png_opacite

TAILLE_SPRITE_DEFAUT: Tuple[int, int] = (128, 128)

class Projectile:
    def __init__(self, angle: float, profondeur: float, z: int) -> None:
        self.angle: float = angle
        self.profondeur: float = profondeur
        self.z: int = z
        self.sprites: List[np.ndarray] = []
        self.current_sprite_index: int = 0

    def setSprite(self, sprites: List[np.ndarray]) -> None:
        self.sprites = sprites
        self.current_sprite_index = 0

    def _calculate_sprite_size(self) -> Tuple[int, int]:
        facteur = max(0.1, (10/self.profondeur))
        return (
            int(TAILLE_SPRITE_DEFAUT[0] * facteur),
            int(TAILLE_SPRITE_DEFAUT[1] * facteur),
        )

    def getCurrentSprite(self) -> Optional[np.ndarray]:
        if not self.sprites:
            return None
        sprite_brut = self.sprites[self.current_sprite_index]
        taille = self._calculate_sprite_size()
        return cv2.resize(sprite_brut, taille)

    def updateFrame(self) -> None:
        if not self.sprites:
            return
        self.current_sprite_index = (self.current_sprite_index + 1) % len(self.sprites)

    def move(self, distance: float) -> None:
        self.profondeur += distance

    def draw(self, fond: np.ndarray) -> np.ndarray:
        sprite = self.getCurrentSprite()
        if sprite is None:
            return fond
        centre_x = fond.shape[1] // 2
        centre_y = fond.shape[0] // 2
        return overlay_png_opacite(fond, sprite, centre_x, centre_y)

    def __repr__(self) -> str:
        return (
            f"Projectile(angle={self.angle}, profondeur={self.profondeur}, "
            f"z={self.z}, frame={self.current_sprite_index}/{len(self.sprites)})"
        )

if __name__ == "__main__":
    projectile = Projectile(angle=45.0, profondeur=10.0, z=0)
    boule_dir = Path(__file__).resolve().parents[1] / "bouleSprite"
    boule: List[np.ndarray] = [
        cv2.imread(str(boule_dir / f"ball_{i}.png"), cv2.IMREAD_UNCHANGED)
        for i in range(1, 9)
    ]
    projectile.setSprite(boule)
    while True:
        fond = np.full((480, 640, 3), 128, dtype=np.uint8)
        projectile.updateFrame()
        cadre = projectile.draw(fond)
        cv2.imshow("Projectile", cadre)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        projectile.move(2)
        print(
            f"Angle: {projectile.angle}, Profondeur: {projectile.profondeur}, Z: {projectile.z}"
        )
        time.sleep(0.2)
    cv2.destroyAllWindows()