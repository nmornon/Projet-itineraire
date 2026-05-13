import cv2
from pathlib import Path
from guerreDesTetes.overlay import overlay_png
from guerreDesTetes.gameUtils.projections import _lidar_to_image

class Ennemi:
    def __init__(self, nom, angle, profondeur, z):
        self.nom = nom
        self.sprite = None
        self.angle = angle          # degrés, dans le repère LiDAR (après correction 180°)
        self.profondeur = profondeur  # mm
        self.z = z                  # mm (hauteur dans le repère LiDAR)

    def setSprite(self, sprite):
        self.sprite = sprite

    def afficher(self, frame):
        """Projette et affiche l'ennemi sur frame. Retourne frame modifié."""
        uv = _lidar_to_image(self.angle, self.profondeur, self.z)
        if uv is None:
            return frame
        u, v = uv
        if self.sprite is not None:
            return overlay_png(frame, self.sprite, u, v)
        # fallback : croix rouge si pas de sprite
        cv2.drawMarker(frame, (u, v), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
        return frame
