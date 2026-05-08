import time
from utils import CSVHandler
from sensors.IMU import read_IMU, initialize_sensors

def get_imu_data(XL_addr, accel_range, accel_freq, gyro_range, gyro_freq, csv_out=None, cond=True):
    """
    Fait l'acquisition des données IMU (accéléromètre et gyroscope) en fonction des paramètres d'acquisition.

    Arguments:
    - XL_addr: l'adresse I2C du LSM6DSO 
    - accel_range: la plage de mesure de l'accéléromètre (g).
    - accel_freq: la fréquence d'échantillonnage de l'accéléromètre (Hz).
    - gyro_range: la plage de mesure du gyroscope (dps).
    - gyro_freq: la fréquence d'échantillonnage du gyroscope (Hz).
    - csv_out: le chemin du fichier CSV d'enregistrement (si définit à None, aucun enregistrement n'est effectué)
    """

    # Calculer l'intervalle en secondes (en fonction de la fréquence)
    interval = 1 / min(accel_freq,gyro_freq)

    # Création du fichier CSV d'enregistrement
    #save_csv = False
    #if csv_out is not None:
    #    save_csv = True
    #    if not csv_out.endswith('.csv'):
    #        csv_out += '.csv'
    #    record = CSVHandler(csv_out)
    #    record.create_csv_with_header(['Timestamp', 'Accel X', 'Accel Y', 'Accel Z', 'Gyro X', 'Gyro Y', 'Gyro Z'])

    # Initialisation des capteurs
    initialize_sensors(XL_addr, accel_range, accel_freq, gyro_range, gyro_freq)

            # Lecture des données
    return 
