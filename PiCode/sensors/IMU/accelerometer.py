import smbus
import time
from config import OUTX_L_A, CONFIG_XL_FREQ, CONFIG_XL_RANGE, CONFIG_XL_SENSITIVITY

def accelerometer_configuration(accel_range, accel_freq):
    """
    Configure les paramètres du LSM6DSO pour l'accéléromètre.

    Arguments: 
    - accel_range: la range de l'accéléromètre
    - accel_freq: la fréquence d'acquisition de l'accéléromètre

    Résultat : l'octet à écrire dans le registre CTRL1_XL pour configurer l'accéléromètre
    """
    # Configuration de l'accéléromètre
    # A COMPLETER
    bit1 = CONFIG_XL_FREQ[accel_freq]
    bit2 = CONFIG_XL_RANGE[accel_range]
    #print(bit1 * (2 ** 4) + bit2 * (2 ** 2))
    return bit1 * (2 ** 4) + bit2 * (2 ** 2)

def read_accelerometer(device_addr, accel_range):
    """
    Lit les données de l'accéléromètre et les convertit.

    Arguments: 
    - device_addr: l'adresse I2C du composant
    - accel_range: la range de l'accéléromètre

    Résultat: les données acquises par de l'accéléromètre en unité physique sur les 3 axes
    """
    from sensors.IMU import read_raw_data
    x, y, z = read_raw_data(device_addr, OUTX_L_A)

    # A COMPLETER
    sensitivity = CONFIG_XL_SENSITIVITY[accel_range]/1000
    return x * sensitivity, y * sensitivity, z * sensitivity
