import cv2
import numpy as np
from guerreDesTetes.overlay import overlay_png
from guerreDesTetes.gameUtils.projections import *
from guerreDesTetes.gameUtils.imu_position_tracking import get_imu_H_w_to_lidar

TAILLE_SPRITE_DEFAUT = (128, 128)

class Entity:
    def __init__(self, nom, position=[0, 0, 0], sprites=None):
        self.nom = nom
        self.sprites = sprites
        self.current_sprite_index = 0
        self._position = {"theta": position[0] % 360, "r": position[1], "z": position[2]} # coordonnées polaires (angle en degrés, profondeur en mm, z en mm)

    def updateFrame(self) -> None:
        if not self.sprites:
            return
        self.current_sprite_index = (self.current_sprite_index + 1) % len(self.sprites)

    def setSprite(self, sprites):
        self.sprites = sprites

    def getPosition(self):
        return self._position

    def setPosition(self, theta, r, z):
        self._position = {"theta": theta % 360, "r": r, "z": z}

    def _calculate_sprite_size(self):
        if (self.getPosition()["r"] == 0) : return (
            int(TAILLE_SPRITE_DEFAUT[0]),
            int(TAILLE_SPRITE_DEFAUT[1]),
        )
        distance = max(1.0, float(self.getPosition()["r"]))
        facteur = max(0.1, min(3.0, 1200.0 / (distance + 200.0)))
        return (
            int(TAILLE_SPRITE_DEFAUT[0] * facteur),
            int(TAILLE_SPRITE_DEFAUT[1] * facteur),
        )
    
    def getCurrentSprite(self):
        if not self.sprites:
            return None
        sprite_brut = self.sprites[self.current_sprite_index]
        self.updateFrame()
        taille = self._calculate_sprite_size()
        return cv2.resize(sprite_brut, taille)

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
            return overlay_png(frame, self.getCurrentSprite(), u, v)
        cv2.drawMarker(frame, (u, v), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
        return frame

    def render(self, frame, lidar_map):
        """Affiche l'ennemi sur la frame et la carte LiDAR. Retourne frame modifié."""
        frame = self.render_image(frame)
        lidar_map = self.render_lidar_map(lidar_map)
        return frame

    def render_lidar_map(self, lidar_map, color=(0, 0, 255)):
        """Affiche l'ennemi sur la carte LiDAR. Retourne lidar_map modifié."""
        pos = self.getPosition()
        x = int(pos["r"] * math.sin(math.radians(pos["theta"])) / 100) + lidar_map.shape[1] // 2
        y = int(pos["r"] * math.cos(math.radians(pos["theta"])) / 100)
        z = int(pos["z"] / 100)
        cv2.circle(lidar_map, (x, lidar_map.shape[0] // 2 - y), max(5, min(20, 2000 // pos["r"])), color, -1)
        return lidar_map


class Ennemi(Entity):
    def __init__(self, nom, angle, profondeur, z, vie=3, sprites=None):
        super().__init__(nom, [angle, profondeur, z], sprites=sprites)
        self.vie = vie

    def wander(self, power=1):
        """Fait bouger l'ennemi de manière aléatoire"""
        self._position["theta"] = (self._position["theta"] + np.random.uniform(-5, 5) * power) % 360
        self._position["r"] = max(500, min(5000, self._position["r"] + np.random.uniform(-100, 100) * power))
        self._position["z"] = max(-500, min(500, self._position["z"] + np.random.uniform(-20, 20) * power))

    def render_lidar_map(self, lidar_map):
        """Affiche l'ennemi sur la carte LiDAR. Retourne lidar_map modifié."""
        super().render_lidar_map(lidar_map, color=(0, 0, 255) if self.vie > 0 else (128, 128, 128))


