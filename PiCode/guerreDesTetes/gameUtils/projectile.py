# PiCode/guerreDesTetes/gameUtils/projectile.py
SPRITE_DEFAULT_SIZE = (128, 128)

import cv2
import time
from pathlib import Path
import numpy as np

class Projectile:
    def __init__(self, angle, profondeur, z):
        self.sprites = []
        self.sprite_size = SPRITE_DEFAULT_SIZE
        self.current_frame_index = 0
        self.angle = angle
        self.profondeur = profondeur
        self.z = z

    def setSprite(self, sprites):
        self.sprites = sprites

    def _calculate_sprite_size(self, sprite_frame):
        scale_factor = max(0.001, 1 - self.profondeur / 100)
        return (int(SPRITE_DEFAULT_SIZE[0] * scale_factor), int(SPRITE_DEFAULT_SIZE[1] * scale_factor))

    def updateFrame(self):
        self.current_frame_index += 1
        if self.current_frame_index >= len(self.sprites):
            self.current_frame_index = 0

    def move(self, distance):
        self.profondeur += distance
    
    def ennemiTouche(self, ennemis):
        for ennemi in ennemis:
            if abs(self.angle - ennemi.angle) < 10 and abs(self.profondeur - ennemi.profondeur) < 10:
                return ennemi
        return None
    
    def draw(self, frame):
        if not self.sprites:
            return frame

        sprite_frame = self.sprites[self.current_frame_index]
        self.sprite_size = self._calculate_sprite_size(sprite_frame)
        resized_sprite = cv2.resize(sprite_frame, self.sprite_size)

        x = frame.shape[1] // 2
        y = frame.shape[0] // 2 

        return overlay_png(frame, resized_sprite, x, y)

# Overlay qui gère la transparence des PNGs (pour les sprites)
def overlay_png(background, overlay, cx, cy):
    h, w = overlay.shape[:2]
    
    x = cx - w // 2
    y = cy - h // 2
    
    bgr = overlay[:, :, :3]
    alpha = overlay[:, :, 3] / 255.0

    roi = background[y:y+h, x:x+w]

    for c in range(3):
        roi[:, :, c] = alpha * bgr[:, :, c] + (1 - alpha) * roi[:, :, c]

    background[y:y+h, x:x+w] = roi
    return background

if __name__ == "__main__":
    projectile = Projectile(45, 10, 0)
    boule_dir = Path(__file__).parent.parent / "bouleSprite"
    
    boule = [
        cv2.imread(str(boule_dir / 'ball_1.png'), cv2.IMREAD_UNCHANGED),
        cv2.imread(str(boule_dir / 'ball_2.png'), cv2.IMREAD_UNCHANGED),
        cv2.imread(str(boule_dir / 'ball_3.png'), cv2.IMREAD_UNCHANGED),
        cv2.imread(str(boule_dir / 'ball_4.png'), cv2.IMREAD_UNCHANGED),
        cv2.imread(str(boule_dir / 'ball_5.png'), cv2.IMREAD_UNCHANGED),
        cv2.imread(str(boule_dir / 'ball_6.png'), cv2.IMREAD_UNCHANGED),
        cv2.imread(str(boule_dir / 'ball_7.png'), cv2.IMREAD_UNCHANGED),
        cv2.imread(str(boule_dir / 'ball_8.png'), cv2.IMREAD_UNCHANGED)
    ]
    projectile.setSprite(boule)
    
    while True:
        background = np.full((480, 640, 3), 128, dtype=np.uint8)  # Gray color  
        projectile.updateFrame()
        frame = projectile.draw(background)
        cv2.imshow("Projectile", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        projectile.move(5)
        print(f"Angle: {projectile.angle}, Profondeur: {projectile.profondeur}, Z: {projectile.z}")
        time.sleep(0.2)

    cv2.destroyAllWindows()