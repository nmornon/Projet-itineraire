import time
import cv2
import numpy as np

from pathlib import Path
from typing import List, Optional, Tuple
from guerreDesTetes.overlay import overlay_png_opacite, overlay_png
from guerreDesTetes.gameUtils.game import *
from guerreDesTetes.gameUtils.projections import *
from guerreDesTetes.gameUtils import imu_position_tracking

BOULE_DIR = Path(__file__).resolve().parents[1] / "bouleSprite"
BOULE: List[np.ndarray] = [
    cv2.imread(str(BOULE_DIR / f"ball_{i}.png"), cv2.IMREAD_UNCHANGED) for i in range(1, 9)
]

class Projectile(Entity):
    def __init__(self, nom) -> None:
        super().__init__(nom, imu_position_tracking.player_polar_rotation, sprites=BOULE)
        self.current_sprite_index: int = 0

        H_w_to_lidar = imu_position_tracking.get_imu_H_w_to_lidar()
        H_w_to_cam = np.eye(4, dtype=float)
        H_w_to_cam[:3, :3] = R_lidar_to_cam @ H_w_to_lidar[:3, :3]
        H_w_to_cam[:3, 3] = R_lidar_to_cam @ (H_w_to_lidar[:3, 3] - T_lidar_to_cam)

        inv_H_w_to_cam = np.linalg.inv(H_w_to_cam)
        camera_pos = inv_H_w_to_cam[:3, 3]

        #FRAME CENTER DEPEND DE LA RESOLUTION
        frame_center = np.array([320.0, 240.0, 1.0], dtype=float)
        K_inv = np.linalg.inv(K)
        ray_cam = K_inv @ frame_center
        ray_cam /= np.linalg.norm(ray_cam)

        forward_cam = H_w_to_cam[:3, :3].T @ ray_cam
        forward_cam /= np.linalg.norm(forward_cam)

        self.direction = forward_cam

        camera_polar = cartesian_to_polar(*camera_pos)
        self.setPosition(*camera_polar)

    def setSprite(self, sprites: List[np.ndarray]) -> None:
        self.sprites = sprites
        self.current_sprite_index = 0

    def _calculate_sprite_size(self) -> Tuple[int, int]:
        if (self.getPosition()["r"] == 0) : return (
            int(TAILLE_SPRITE_DEFAUT[0]),
            int(TAILLE_SPRITE_DEFAUT[1]),
        )
        distance = max(1.0, float(self.getPosition()["r"]))
        facteur = max(0.1, min(3.0, 1200.0 / (distance*2.5 + 200.0)))
        return (
            int(TAILLE_SPRITE_DEFAUT[0] * facteur),
            int(TAILLE_SPRITE_DEFAUT[1] * facteur),
        )

    def getCurrentSprite(self):
        if not self.sprites:
            return None
        sprite_brut = self.sprites[self.current_sprite_index]
        taille = self._calculate_sprite_size()
        return cv2.resize(sprite_brut, taille)

    def updateFrame(self) -> None:
        if not self.sprites:
            return
        self.current_sprite_index = (self.current_sprite_index + 1) % len(self.sprites)

    def move(self, vitesse: float) -> None:
        pos_cart = polar_to_cartesian(self.getPosition()["theta"], self.getPosition()["r"], self.getPosition()["z"])
        pos_cart += self.direction * vitesse
        new_polar = cartesian_to_polar(*pos_cart)
        self.setPosition(*new_polar)

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
        if self.sprites is not None:
            return overlay_png_opacite(frame, self.getCurrentSprite(), u, v)
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