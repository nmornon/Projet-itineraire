import cv2
import numpy as np
from guerreDesTetes.overlay import overlay_png
from guerreDesTetes.gameUtils.projections import _lidar_to_image

class Entity:
    def __init__(self, nom, position=[0, 0, 0], sprite=None):
        self.nom = nom
        self.sprite = sprite
        self._position = np.array(position)

    def setSprite(self, sprite):
        self.sprite = sprite

    def getPosition(self):
        return self._position

    def setPosition(self, r, teta, z):
        self._position = np.array([r, teta, z])

class Ennemi(Entity):
    def __init__(self, nom, angle, profondeur, z, vie=3, sprite=None):
        super().__init__(nom, [angle, profondeur, z], sprite=sprite)
        self.vie = vie

    def afficher(self, frame):
        """Projette et affiche l'ennemi sur frame. Retourne frame modifié."""
        u, v = project_point_world_to_image(self.getPosition())
        if u is None or v is None:
            return frame
        print(f"Ennemi {self.nom} projeté en (u={u}, v={v})")
        if self.sprite is not None:
            return overlay_png(frame, self.sprite, u, v)
        cv2.drawMarker(frame, (u, v), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
        return frame
