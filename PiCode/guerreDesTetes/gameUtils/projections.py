import math
import numpy as np

# Calibration caméra
_cal = "images/camera_calibration.npz"
_K    = _cal["camera_matrix"]
_DIST = _cal["dist_coeffs"]

# Position de la caméra dans le repère LiDAR (mm)
_T_CAM_IN_LIDAR = np.array([32.0, 124.0, 0.0]) # mesures récup distance caméra-LiDAR

# Rotation LiDAR à Caméra
# LiDAR (après correction 180°) : X=droite, Y=avant, Z=haut
# Caméra OpenCV                 : X=droite, Y=bas,   Z=profondeur
_R_L_TO_C = np.array([
    [1,  0,  0],   # x_cam =  x_L
    [0,  0, -1],   # y_cam = -z_L
    [0,  1,  0],   # z_cam =  y_L
], dtype=np.float64)

def _lidar_to_image(angle_deg, profondeur_mm, z_mm):
    """Projette un point LiDAR (polaire 3D) vers les coordonnées pixel image.
    Retourne (u, v) ou None si le point est derrière la caméra."""
    rad = math.radians(angle_deg)
    p_L = np.array([
        profondeur_mm * math.cos(rad),
        profondeur_mm * math.sin(rad),
        z_mm,
    ])

    p_C = _R_L_TO_C @ (p_L - _T_CAM_IN_LIDAR)

    if p_C[2] <= 0:
        return None

    pts_2d, _ = cv2.projectPoints(
        p_C.reshape(1, 1, 3).astype(np.float64),
        np.zeros(3), np.zeros(3),
        _K, _DIST,
    )
    u, v = pts_2d[0, 0]
    return int(round(u)), int(round(v))
