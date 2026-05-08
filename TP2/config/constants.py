# A COMPLETER

# Adresses I2C et USB des composants
LSM6DSO_ADDR = 0x6b               # Adresse I2C du capteur LSM6DSO (Accéléromètre/Gyroscope)
LIS3MDL_ADDR = 0x1e               # Adresse I2C du capteur LIS3MDL (Magnétomètre)

# Constantes des registres de configuration de l'IMU
CTRL1_XL = 0x10                   # Registre de configuration de l'accéléromètre
CTRL2_G = 0x11                    # Registre de configuration du gyroscope
OUTX_L_A = 0x28                   # Registre de lecture de l'accéléromètre
OUTX_L_G = 0x22                   # Registre de lecture du gyroscope

# Mappages des fréquences (Hz) pour l'accéléromètre
CONFIG_XL_FREQ = {0:0b0000,1.6:0b1011,12.5:0b0001,26:0b0010,52:0b0011,104:0b0100,208:0b0101,416:0b0110,833:0b0111,1660:0b1000,3330:0b1001,6660:0b1010}

# Mappages des plages (full-scale range) pour l'accéléromètre
CONFIG_XL_RANGE = {2:0b00,16:0b01,4:0b10,8:0b11}

# Sensibilités des capteurs pour conversion des données brutes en unités physiques
CONFIG_XL_SENSITIVITY = {2:0.061,4:0.122,8:0.244,16:0.488}

# Mappages des fréquences (Hz) pour le gyroscope
CONFIG_G_FREQ = {0:0b0000,12.5:0b0001,26:0b0010,52:0b0011,104:0b0100,208:0b0101,416:0b0110,833:0b0111,1660:0b1000,3330:0b1001,6660:0b1010}

# Mappages des plages (full-scale range) pour le gyroscope
CONFIG_G_RANGE = {250:0b00,500:0b01,1000:0b10,2000:0b11}

# Sensibilités des capteurs pour conversion des données brutes en unités physiques
CONFIG_G_SENSITIVITY = {125:4.375,250:8.75,500:17.50,1000:35,2000:70}
