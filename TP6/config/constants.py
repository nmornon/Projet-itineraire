# Ports GPIO
PORT_LIDAR = "/dev/ttyUSB0"      # Port USB connecté au LiDAR
PORT_BUTTON = 18 # Port GPIO du Bouton
PORT_LED = 16 # Port GPIO de la LED

# Constantes de configuration du LiDAR
LIDAR_MIN_RANGE = 150                  # Portée minimale du LiDAR en mm
LIDAR_MAX_RANGE = 12000                # Portée maximale du LiDAR en mm

ACQUISITION_ROOT = 'data/'

DISPLAY_SIZE = (1080, 720) # Taille d'affichage par défaut de la fenêtre

# Constantes de calibration
DIM_GRID = (7,6) # Dimension de la grille d'échecs (nombre de coins intérieurs par ligne et par colonne)
SQUARE_SIZE = 20 # Taille du carré en mm