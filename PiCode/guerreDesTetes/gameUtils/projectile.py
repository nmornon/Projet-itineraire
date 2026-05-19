import time
import cv2
import numpy as np

from pathlib import Path
from typing import List, Optional, Tuple
from guerreDesTetes.overlay import overlay_png_opacite, overlay_png
from guerreDesTetes.gameUtils.game import Entity
from guerreDesTetes.gameUtils.projections import *
from guerreDesTetes.gameUtils.imu_position_tracking import get_imu_H_w_to_lidar

TAILLE_SPRITE_DEFAUT: Tuple[int, int] = (128, 128)
BOULE_DIR = Path(__file__).resolve().parents[1] / "bouleSprite"
BOULE: List[np.ndarray] = [
    cv2.imread(str(BOULE_DIR / f"ball_{i}.png"), cv2.IMREAD_UNCHANGED)
    for i in range(1, 9)
]

class Projectile(Entity):
    def __init__(self, nom, position=[0,0,0], sprite=BOULE) -> None:
        super().__init__(nom, position, sprite)
        self.current_sprite_index: int = 0

    def setSprite(self, sprites: List[np.ndarray]) -> None:
        self.sprite = sprites
        self.current_sprite_index = 0

    def _calculate_sprite_size(self) -> Tuple[int, int]:
        facteur = max(0.1, (10/self.getPosition()["z"]))
        return (
            int(TAILLE_SPRITE_DEFAUT[0] * facteur),
            int(TAILLE_SPRITE_DEFAUT[1] * facteur),
        )

    def getCurrentSprite(self) -> Optional[np.ndarray]:
        if not self.sprite:
            return None
        sprite_brut = self.sprites[self.current_sprite_index]
        taille = self._calculate_sprite_size()
        return cv2.resize(sprite_brut, taille)

    def updateFrame(self) -> None:
        if not self.sprite:
            return
        self.current_sprite_index = (self.current_sprite_index + 1) % len(self.sprite)

    def move(self, distance: float) -> None:
        self.getPosition()["r"] += distance
    
    def render_image(self, frame):
        """Projette et affiche l'ennemi sur frame. Retourne frame modifié."""
        pos = self.getPosition()
        result = project_point_world_to_image(
            polar_to_cartesian(
                pos["theta"], pos["r"], pos["z"]
                ),
             H_w_to_lidar=get_imu_H_w_to_lidar())

        if result is None:
            return frame
        u, v = result
        #print(f"Ennemi {self.nom} projeté en (u={u}, v={v}), angle ={pos['theta']:.1f}°, profondeur={pos['r']:.1f}mm")
        if self.sprite is not None:
            return overlay_png(frame, self.getCurrentSprite(), u, v)
        return frame

    def __repr__(self) -> str:
        return (
            f"Projectile(angle={self.angle}, profondeur={self.profondeur}, "
            f"z={self.z}, frame={self.current_sprite_index}/{len(self.sprites)})"
        )

if __name__ == "__main__":
    projectile = Projectile(nom="TestProjectile", position=[0, 10.0, 0])
    # fonctionne pas
    while True:
        fond = np.full((480, 640, 3), 128, dtype=np.uint8)
        projectile.updateFrame()
        cadre = projectile.render_image(fond)
        cv2.imshow("Projectile", cadre)
        projectile.move(2)

        pos = projectile.getPosition()
        print(f"Angle: {pos['theta']}, Profondeur: {pos['r']}, Z: {pos['z']}" )
        time.sleep(0.2)