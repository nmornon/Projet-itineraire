
import numpy as np
import cv2
from guerreDesTetes.gameUtils.projections import create_transformation_matrix 
R_world_to_lidar = np.eye(3)  # Matrice de rotation du monde à l'IMU
T_world_to_lidar = np.zeros(3)  # Translation du monde à l'IMU


def update_imu_position_tracking(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z):
    """Met à jour la position de l'IMU en fonction des données reçues."""
    global R_world_to_lidar, T_world_to_lidar

    accel = (np.array([accel_x, accel_y, accel_z]) / 1000.0)  # Convertir de mm/s2 à m/s2
    gyro = np.radians(np.array([gyro_x, gyro_y, gyro_z]))  # Convertir deg/s à radians/s

    # Mettre à jour la matrice de rotation en fonction des vitesses angulaires
    dt = 0.03
    angle_change = gyro * dt
    R_delta = np.eye(3)
    cv2.Rodrigues(angle_change,R_delta)
    print(np.degrees(R_delta))
    R_world_to_lidar = R_delta @ R_world_to_lidar

    # Mettre à jour la position en fonction de l'accélération
    T_world_to_lidar += R_world_to_lidar @ accel * dt**2 / 2  # Intégration double pour la position

def get_imu_H_w_to_lidar():
    """Retourne la matrice de transformation homogène du monde à l'IMU."""
    return create_transformation_matrix(R_world_to_lidar, T_world_to_lidar)
