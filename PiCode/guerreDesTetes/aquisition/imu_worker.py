import time

from sensors.IMU import initialize_sensors, read_IMU
from config import LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ


def imu_worker(state, lock, stop_event):
    """Thread IMU : stocke la dernière mesure dans state['latest_imu']."""
    try:
        initialize_sensors(LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ)
    except Exception as e:
        print(f"[imu] Initialisation échouée : {e}")

    while not stop_event.is_set():
        try:
            imu_data = read_IMU(LSM6DSO_ADDR, ACCEL_RANGE, GYRO_RANGE)
            with lock:
                state["latest_imu"] = imu_data
        except Exception as e:
            print(f"[imu] Erreur lecture : {e}")
        time.sleep(0.02) 
