import os

_HAAR_PATHS = [
    '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
    '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml',
    '/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
]

_cascade_path = next((p for p in _HAAR_PATHS if os.path.exists(p)), None)
if _cascade_path is None:
    raise FileNotFoundError("haarcascade_frontalface_default.xml introuvable")

_face_cascade = cv2.CascadeClassifier(_cascade_path)