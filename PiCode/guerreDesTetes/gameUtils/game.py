import cv2
from pathlib import Path
from guerreDesTetes.overlay import overlay_png
from guerreDesTetes.gameUtils.projections import _lidar_to_image

class Entity:
    _position = np.array([0, 0, 0]) # r, teta, z dans le repère monde
    def __init__(self, nom, position=[0, 0, 0]):
        self.nom = nom
        self.sprite = None
        self._position = np.array(position)

    def setSprite(self, sprite):
        self.sprite = sprite

    def getPosition(self):
        return self._position
    
    def setPosition(self, position):
        self._position = position

    def setPosition(self, r, teta, z):
        self._position = np.array([r, teta, z])

class Enemy(Entity):
        def __init__(self, nom, position=[0, 0, 0], vie=3):
            super().__init__(nom, position)
            self.vie = vie

    def setSprite(self, sprite):
        self.sprite = sprite

    def afficher(self, frame):
        """Projette et affiche l'ennemi sur frame. Retourne frame modifié."""
        uv = _lidar_to_image(self.angle, self.profondeur, self.z)
        if uv is None:
            return frame
        u, v = uv
        print(f"Ennemi {self.nom} projeté en (u={u}, v={v})")
        if self.sprite is not None:
            return overlay_png(frame, self.sprite, u, v)
        # fallback : croix rouge si pas de sprite
        cv2.drawMarker(frame, (u, v), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
        return frame
