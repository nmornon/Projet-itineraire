import cv2
import numpy as np

SPRITE_SIZE = 128   # taille du sprite carré en sortie (pixels)

_face_cascade = cv2.CascadeClassifier(
    '/home/pi/env13_capteurs/lib/python3.13/site-packages/cv2/data/haarcascade_frontalface_default.xml'
)

def capture_face_sprite(frame):
    """
    Recup une photo et la transforme en visage.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = _face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=8,
        minSize=(80, 80)
    )

    # Rien détecté
    if len(faces) == 0:
        print("[capture] Aucun visage détecté.")
        return None

    # Premier visage détecté
    x_min, y_min, box_width, box_height = faces[0]

    print(f"[capture] Visage détecté : x={x_min} y={y_min} w={box_width} h={box_height}")

    # Extraction du visage
    face = frame[y_min:y_min + box_height, x_min:x_min + box_width]
    face = cv2.resize(face, (SPRITE_SIZE, SPRITE_SIZE), interpolation=cv2.INTER_AREA)

    sprite = cv2.cvtColor(face, cv2.COLOR_BGR2BGRA)
    alpha = np.zeros((SPRITE_SIZE, SPRITE_SIZE), dtype=np.uint8)
    axes = (int(SPRITE_SIZE * 0.42), int(SPRITE_SIZE * 0.49))
    cv2.ellipse(
        alpha,
        (SPRITE_SIZE // 2, SPRITE_SIZE // 2),
        axes,
        0,
        0,
        360,
        255,
        -1,
        lineType=cv2.LINE_AA,
    )
    sprite[:, :, 3] = alpha

    print(f"[capture] Sprite pret ({SPRITE_SIZE}x{SPRITE_SIZE} px).")
    return sprite


if __name__ == "__main__":
    selfie = cv2.imread("guerreDesTetes/selfies/selfie_000.jpg")
    sprite = capture_face_sprite(selfie)
    if sprite is not None:
        cv2.imshow("Sprite", sprite)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
