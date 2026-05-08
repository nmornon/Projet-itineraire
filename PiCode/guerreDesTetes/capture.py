import cv2
import numpy as np
import mediapipe as mp

SPRITE_SIZE = 128   # taille du sprite carré en sortie (pixels)


def capture_face_sprite(frame):
    """
    Récupère une photo et la transforme en visage
    """

    # Je tente de détecter le vizage
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #mediapipe utilise du rgb

    with mp.solutions.face_detection.FaceDetection(min_detection_confidence=0.5) as detector:
        result = detector.process(rgb)

    #Rien détecté
    if not result.detections:
        print("[capture] Aucun visage détecté.")
        return None


    detection_box = result.detections[0].location_data.relative_bounding_box

    print(detection_box)
    # Convertion en pixels
    x_min = int(detection_box.xmin * w)
    y_min = int(detection_box.ymin * h)
    box_width = int(detection_box.width * w)
    box_height = int(detection_box.height * h)

    # Extraction du visage
    sprite = frame[y_min:y_min + box_height, x_min:x_min + box_width]
    sprite = cv2.resize(sprite, (SPRITE_SIZE, SPRITE_SIZE), interpolation=cv2.INTER_AREA)

    print(f"[capture] Sprite prêt ({SPRITE_SIZE}x{SPRITE_SIZE} px).")
    return sprite

if __name__ == "__main__":
    selfie = cv2.imread("guerreDesTetes/selfies/selfie_001.jpg")
    sprite = capture_face_sprite(selfie)
    if sprite is not None:
        cv2.imshow("Sprite", sprite)
        cv2.waitKey(0)
        cv2.destroyAllWindows()