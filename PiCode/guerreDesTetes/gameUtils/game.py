import cv2
import numpy as np
from guerreDesTetes.overlay import overlay_png
from guerreDesTetes.gameUtils.projections import *

class Entity:
    def __init__(self, nom, position=[0, 0, 0], sprite=None):
        self.nom = nom
        self.sprite = sprite
        self._position = {"theta": position[0] % 360, "r": position[1], "z": position[2]} # coordonnées polaires (angle en degrés, profondeur en mm, z en mm)

    def setSprite(self, sprite):
        self.sprite = sprite

    def getPosition(self):
        return self._position

    def setPosition(self, theta, r, z):
        self._position = {"theta": theta % 360, "r": r, "z": z}
    

class Ennemi(Entity):
    def __init__(self, nom, angle, profondeur, z, vie=3, sprite=None):
        super().__init__(nom, [angle, profondeur, z], sprite=sprite)
        self.vie = vie

    def wander(self, power=1):
        """Fait bouger l'ennemi de manière aléatoire"""
        self._position["theta"] = (self._position["theta"] + np.random.uniform(-5, 5) * power) % 360
        self._position["r"] = max(500, min(5000, self._position["r"] + np.random.uniform(-100, 100) * power))
        self._position["z"] = max(-500, min(500, self._position["z"] + np.random.uniform(-20, 20) * power))

    def _render_image(self, frame):
        """Projette et affiche l'ennemi sur frame. Retourne frame modifié."""
        pos = self.getPosition()
        result = project_point_world_to_image(polar_to_cartesian(
            pos["theta"], pos["r"], pos["z"]
        ))
        if result is None:
            return frame
        u, v = result
        #print(f"Ennemi {self.nom} projeté en (u={u}, v={v}), angle ={pos['theta']:.1f}°, profondeur={pos['r']:.1f}mm")
        if self.sprite is not None:
            return overlay_png(frame, self.sprite, u, v)
        cv2.drawMarker(frame, (u, v), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
        return frame

    def _render_lidar_map(self, lidar_map):
        """Affiche l'ennemi sur la carte LiDAR. Retourne lidar_map modifié."""
        pos = self.getPosition()
        x = int(pos["r"] * math.sin(math.radians(pos["theta"])) / 100) + lidar_map.shape[1] // 2
        y = int(pos["r"] * math.cos(math.radians(pos["theta"])) / 100)
        z = int(pos["z"] / 100)
        color = (0, 0, 255) if self.vie > 0 else (128, 128, 128)
        cv2.circle(lidar_map, (x, lidar_map.shape[0] // 2 - y), max(5, min(20, 2000 // pos["r"])), color, -1)
        return lidar_map

    def render(self, frame, lidar_map):
        """Affiche l'ennemi sur la frame et la carte LiDAR. Retourne frame modifié."""
        frame = self._render_image(frame)
        lidar_map = self._render_lidar_map(lidar_map)
        return frame
