import time
import shutil
import argparse
import traceback
import threading
from pathlib import Path
from core.calibration import load_calibration, undistort_image
from sensors.CAMERA import Camera
from sensors.LIDAR import LIDAR
from sensors.GNSS import GNSS
from sensors.IMU import imu,initialize_sensors, read_IMU
from core.imu_acquisition import get_imu_data
from core.gnss_position import gnss_position
from utils import Button, LED, create_acquisition_directory, CSVHandler
from utils import CSVHandler
from utils.LCD import LCD
from config import*
from sensors.IMU.magnetometer import read_magnetometer

ACQUISITION_PATH = Path(ACQUISITION_ROOT)


def start_acquisition(state, led):
    """
    Lance une acquisition multisenseur :
    - création du dossier session
    - création des sous-dossiers images / scans
    - création des CSV de timestamps
    """
    session_dir, subdirs = create_acquisition_directory(
        root_dir=ACQUISITION_ROOT,
        prefix="acquisition",
        subdirs=["images", "scans", "gnss", "imu"]
    )

    state["is_acquiring"] = True
    state["session_dir"] = session_dir
    state["images_dir"] = subdirs["images"]
    state["scans_dir"] = subdirs["scans"]
    state["gnss_dir"] = subdirs["gnss"]
    state["imu_dir"] = subdirs["imu"]   
    state["frame_index"] = 0
    state["scan_index"] = 0
    state["gnss_index"] = 0
    state["imu_index"] = 0

    # A COMPLETER
    # Copie du fichier config/parameters.py dans le dossier d'acquisition
    shutil.copy(Path(__file__).parent.parent / "config/parameters.py", session_dir / "parameters.py")

    # Création des fichiers CSV timestamps/frames et timestamps/scans
    path_frames = session_dir / "timestamps_frames.csv"
    csv_frames = CSVHandler(str(path_frames))
    csv_frames.create_csv_with_header(header=["timestamp", "image_file"])

    path_scans = session_dir / "timestamps_scans.csv"
    csv_scans = CSVHandler(str(path_scans))
    csv_scans.create_csv_with_header(header=["timestamp", "scan_file"])

    path_gnss = session_dir / "gnss.csv"
    csv_gnss = CSVHandler(str(path_gnss))
    csv_gnss.create_csv_with_header(header=["timestamp", "latitude", "longitude","hdop","vdop","pdop"])

    path_imu = session_dir / "imu.csv"
    csv_imu = CSVHandler(str(path_imu))
    csv_imu.create_csv_with_header(header=["timestamp", "accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z","mag_x","mag_y","mag_z"])

    # Ajout des CSVHandlers créés dans state (pour y accéder en dehors de la fonction)
    state["csv_frames"] = csv_frames
    state["csv_scans"] = csv_scans
    state["csv_gnss"] = csv_gnss
    state["csv_imu"] = csv_imu

    led.on()
    print(f"Acquisition démarrée : {session_dir}")


def stop_acquisition(state, led, reason=None):
    """
    Arrête l'acquisition en cours et remet l'état session à zéro.
    """
    if reason is not None:
        print(f"Acquisition interrompue : {reason}")
    elif state["session_dir"] is not None:
        print(f"Acquisition arrêtée : {state['session_dir']}")

    state["is_acquiring"] = False
    state["session_dir"] = None
    state["images_dir"] = None
    state["scans_dir"] = None
    state["gnss_dir"] = None
    state["imu_dir"] = None
    state["frame_index"] = 0
    state["scan_index"] = 0
    state["gnss_index"] = 0
    state["imu_index"] = 0
    state["csv_frames"] = None
    state["csv_scans"] = None
    state["csv_gnss"] = None
    state["csv_imu"] = None
    led.off()


def toggle_acquisition(state, led, lock):
    """
    Démarre ou arrête une acquisition.
    """
    with lock:
        if not state["is_acquiring"]:
            start_acquisition(state, led)
        else:
            stop_acquisition(state, led)


def gnss_worker(state, lock, stop_event):
    """
    Thread d'acquisition GNSS .
    """
    gnss = GNSS(1, GNSS_DEVICE_ADDR)
    gnss.initialisation(GNSS_MODES[MODE_GNSS])
    lcd_display = LCD(LCD_DEVICE_ADDR)
    while not stop_event.is_set():
        # Lecture d'une acquisition GNSS (timestamp, latitude, longitude, altitude)
        
        timestamp = time.time()

        # Récupération du prochain scan GPS
        gnss.wait_for_next_scan(timeout=1.0)

        # Gestion d'un signal mauvais
        if not(gnss.reception_ok):
            if lcd_display is not None:
                lcd_display.afficher("Recherche de    signal GNSS...")
            print("Recherche de signal GNSS...")
            continue
        latitude = gnss.latitude.coordinates_DD
        longitude = gnss.longitude.coordinates_DD
        hdop = gnss.hdop
        vdop = gnss.vdop
        pdop = gnss.pdop
        print(f"Position GNSS : lat={latitude:.6f}, lon={longitude:.6f}")
        lcd_display.effacer()
        lcd_display.afficher(f"Lat:{latitude:.6f}\n\rLon:{longitude:.6f}")

        with lock:
            if state["is_acquiring"]:
                # Mise à jour du fichier timestamp avec la nouvelle acquisition (timestamp et chemin du fichier)
                state["csv_gnss"].append_row([timestamp, latitude, longitude,hdop,vdop,pdop])
                print(f"Acquisition GNSS enregistrée : {timestamp}, {latitude}, {longitude}")
                state["gnss_index"] += 1

        time.sleep(0.1)


def imu_worker(state, lock, stop_event):
    """
    Thread d'acquisition IMU .
    """
    initialize_sensors(LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ)
    while not stop_event.is_set():
        # Lecture d'une acquisition IMU (timestamp, latitude, longitude, altitude)

        
        timestamp = time.time()
        accel_x = 0.0
        accel_y = 0.0
        accel_z = 0.0
        gyro_x = 0.0
        gyro_y = 0.0
        gyro_z = 0.0

        # Mise à jour du fichier timestamp avec la nouvelle acquisition (timestamp et chemin du fichier)
        accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z = read_IMU(LSM6DSO_ADDR, ACCEL_RANGE, GYRO_RANGE)
                
        mag_x, mag_y, mag_z = read_magnetometer(LIS3MDL_ADDR, MAGNETO_RANGE)

        with lock:
            if state["is_acquiring"]:
                
        
                state["csv_imu"].append_row([timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z,mag_x,mag_y,mag_z])
                state["imu_index"] += 1

        time.sleep(0.1)

def camera_worker(camera, calibration, state, lock, stop_event, extension="jpg"):
    """
    Thread d'acquisition caméra.
    """
    while not stop_event.is_set():
        try:
            # A COMPLETER
            # Lecture d'une acquisition caméra
            frame = camera.capture_frame()
            
            if calibration is not None:
                # Correction de la distorsion
                frame = undistort_image(frame, calibration)
                
            timestamp = time.time()

            with lock:
                if state["is_acquiring"]:
                    # A COMPLETER
                    # Enregistrement de l'image
                    image_filename = f"frame_{state['frame_index']:04d}.{extension}"
                    image_filepath = state["images_dir"] / image_filename
                    camera.save_frame(frame, str(image_filepath))

                    # A COMPLETER
                    # Mise à jour du fichier timestamp avec la nouvelle acquisition (timestamp et chemin du fichier)
                    state["csv_frames"].append_row([timestamp, str(image_filepath)])
                    state["frame_index"] += 1

        except Exception:
            traceback.print_exc()
            with lock:
                state["is_acquiring"] = False
                state["session_dir"] = None
                state["images_dir"] = None
                state["scans_dir"] = None
                state["frame_index"] = 0
                state["scan_index"] = 0
                state["csv_frames"] = None
                state["csv_scans"] = None
            time.sleep(0.1)

        time.sleep(0.01)


def lidar_worker(lidar, state, lock, stop_event):
    """
    Thread d'acquisition LiDAR.
    """
    while not stop_event.is_set():
        try:
            # A COMPLETER
            # Lecture d'une acquisition LiDAR
            timestamp, measures, points = lidar.read_scan()

            with lock:
                if state["is_acquiring"]:
                # A COMPLETER
                # Enregistrement de l'acquisition LiDAR
                    scan_filename = f"scan_{state['scan_index']:04d}.csv"
                    scan_filepath = state["scans_dir"] / scan_filename
                    lidar.save_scan(points, str(scan_filepath))

                # A COMPLETER
                # Mise à jour du fichier timestamp avec la nouvelle acquisition (timestamp et chemin du fichier)
                    state["csv_scans"].append_row([timestamp, str(scan_filepath)])
                    state["scan_index"] += 1

        except Exception:
            traceback.print_exc()
            with lock:
                state["is_acquiring"] = False
                state["session_dir"] = None
                state["images_dir"] = None
                state["scans_dir"] = None
                state["frame_index"] = 0
                state["scan_index"] = 0
                state["csv_frames"] = None
                state["csv_scans"] = None
            time.sleep(0.1)

        time.sleep(0.01)


def main(calibration_file=None):
    # print("Initialisation de la caméra...")
    # # Initialisation de la caméra
    # camera = Camera()
    # camera.configure()
    # camera.start()
    # camera.warmup()
    
    # if calibration_file is not None:
    #     print("Chargement de la calibration...")
    #     # Chargement de la calibration
    #     calibration = load_calibration(calibration_file)
    # else:
    #     calibration = None
    
    
    # print("Initialisation du LiDAR...")
    # # Initialisation du LiDAR
    # lidar = LIDAR(PORT_LIDAR,
    #               quality_threshold=QUALITY_THRESHOLD,
    #               min_range=MIN_DETECTION_RANGE,
    #               max_range=MAX_DETECTION_RANGE,
    #                 min_angle=MIN_DETECTION_ANGLE,
    #                 max_angle=MAX_DETECTION_ANGLE)


    # # Démarrage du LiDAR
    # lidar.start()
    
    # # Chauffe du LiDAR (warmup)
    # lidar.warmup(3)
    
    print("Initialisation du bouton...")
    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)

    ACQUISITION_PATH.mkdir(parents=True, exist_ok=True)

    state = {
        "is_acquiring": False,
        "session_dir": None,
        "images_dir": None,
        "scans_dir": None,
        "gnss_dir": None,
        "frame_index": 0,
        "scan_index": 0,
        "gnss_index": 0,
        "csv_frames": None,
        "csv_scans": None,
        "csv_gnss": None,
    }

    lock = threading.Lock()
    stop_event = threading.Event()

    # camera_thread = threading.Thread(
    #     target=camera_worker,
    #     args=(camera, calibration, state, lock, stop_event),
    #     daemon=True
    # )

    # lidar_thread = threading.Thread(
    #     target=lidar_worker,
    #     args=(lidar, state, lock, stop_event),
    #     daemon=True
    # )

    gnss_thread = threading.Thread(
        target=gnss_worker,
        args=(state, lock, stop_event),
        daemon=True
    )

    imu_thread = threading.Thread(
        target=imu_worker,
        args=(state, lock, stop_event),
        daemon=True
    )

    print("Appuyer sur le bouton pour démarrer / arrêter l'acquisition multisenseur.")
    print("Ctrl+C pour quitter.")

    try:
        # camera_thread.start()
        # lidar_thread.start()
        gnss_thread.start()
        imu_thread.start()

        while True:
            if button.is_pressed():
                toggle_acquisition(state, led, lock)
                button.wait_for_release()
                time.sleep(0.05)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nArrêt du programme demandé par l'utilisateur.")

    finally:
        stop_event.set()

        # camera_thread.join(timeout=1.0)
        # lidar_thread.join(timeout=1.0)
        gnss_thread.join(timeout=1.0)
        imu_thread.join(timeout=1.0)

        led.off()
        button.cleanup()
        led.cleanup()
        # camera.stop()
        # lidar.stop()

        print("Ressources libérées.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Acquisition multisenseur caméra + LiDAR."
    )

    parser.add_argument("--calibration_file", type=str, help="Fichier de calibration.")

    args = parser.parse_args()

    main(args.calibration_file)
