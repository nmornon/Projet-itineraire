
import numpy as np
import cv2
import time
from guerreDesTetes.gameUtils.projections import create_transformation_matrix 
R_world_to_lidar = np.eye(3)  # Matrice de rotation du monde à l'IMU
T_world_to_lidar = np.zeros(3)  # Translation du monde à l'IMU
player_polar_rotation = np.zeros(3)

last_update_time = time.time()

def Rz(angle):
    return np.array([
        [np.cos(angle),-np.sin(angle),0],
        [np.sin(angle),np.cos(angle),0],
        [0,0,1]
    ])

def Rx(angle):
    return np.array([
        [1,0,0],
        [0,np.cos(angle),-np.sin(angle)],
        [0,np.sin(angle),np.cos(angle)]
    ])

def Ry(angle):
    return np.array([
        [np.cos(angle),0,np.sin(angle)],
        [0,1,0],
        [-np.sin(angle),0,np.cos(angle)]
    ])

def update_imu_position_tracking(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z):
    """Met à jour la position de l'IMU en fonction des données reçues."""
    global R_world_to_lidar, T_world_to_lidar, last_update_time,player_polar_rotation

    accel = (np.array([accel_x, accel_y, accel_z]) / 1000.0)  # Convertir de mm/s2 à m/s2
    gyro = np.radians(np.array([gyro_x, gyro_y, gyro_z]))
    # Mettre à jour la matrice de rotation en fonction des vitesses angulaires
    dt = last_update_time - time.time()
    last_update_time = time.time()



    angle_change = gyro * dt
    R_delta = Rz(angle_change[0])@ Ry(angle_change[2]) @Rx(angle_change[1])
    player_polar_rotation += np.degrees(angle_change)

    R_world_to_lidar = R_world_to_lidar @ R_delta
    # Mettre à jour la position en fonction de l'accélération
    T_world_to_lidar = accel * dt**2 / 2  # Intégration double pour la position

def get_imu_H_w_to_lidar():
    """Retourne la matrice de transformation homogène du monde à l'IMU."""
    return create_transformation_matrix(R_world_to_lidar, T_world_to_lidar)
