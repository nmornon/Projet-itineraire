import math
import numpy as np
import cv2
from pathlib import Path

# Recup des donnees de calibration caméra
CALIBRATION_PATH = Path(__file__).resolve().parents[2] / "images" / "camera_calibration.npz"
with np.load(CALIBRATION_PATH) as cal:
    K = cal["camera_matrix"].copy()
    DIST = cal["dist_coeffs"].copy()
 
# Position de la caméra dans le repère LiDAR (mm)
T_lidar_to_cam = np.array([32.0, 124.0, 0.0]) # mesures récup distance caméra-LiDAR

# Rotation LiDAR à Caméra
# LiDAR (après correction 180°) : X=droite, Y=avant, Z=haut
# Caméra OpenCV                 : X=droite, Y=bas,   Z=profondeur
R_lidar_to_cam = np.array([
    [1,  0,  0],   # x_cam =  x_L
    [0,  0, -1],   # y_cam = -z_L
    [0,  1,  0],   # z_cam =  y_L
], dtype=np.float64)

def set_world_repere():
    #a completer
    pass

def addtuple(a,b):
    return tuple(map(sum,zip(a,b)))

def create_transformation_matrix(R, T):
    """Crée la matrice de transformation (R | T)"""
    mat = np.zeros(addtuple(R.shape,(1,1)))
    n,p = mat.shape
    mat[:3,:p-1] = R
    mat[:3,p-1:] = T.reshape((3,1))
    mat[3:,p-1:] = np.ones((1,1))
    return mat

def project_point_world_to_image(point_world, H_w_to_lidar): # H la matrice de transformation (R T | 0 1)
    """Projette un point du repère monde vers l'image caméra."""
    point_lidar = H_w_to_lidar @ np.append(point_world, 1)

    

if __name__ == "__main__":
    # Test rapide
    print("=== Test de projection LiDAR -> Image ===")
    test_points = [
        (0, 1, 0),   # devant
        (90, 1000, 0),  # à droite
        (-90, 1000, 0), # à gauche
        (180, 1000, 0), # derrière
        (45, 1414, 0),  # diagonale avant-droite
    ]
    
    for angle, depth, z in test_points:
        print(f"Test: angle={angle}°, profondeur={depth}mm, z={z}mm")
        pixel = project_point_world_to_image(np.array([angle, depth, z]), H)
        print(f"Résultat: {pixel}\n{'-'*40}\n")