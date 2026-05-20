import argparse
import threading
from pathlib import Path

from sensors.CAMERA import Camera
from sensors.LIDAR import LIDAR
from utils import Button, LED
from config import (
    PORT_BUTTON, PORT_LED,
    PORT_LIDAR,
    MIN_DETECTION_RANGE, MAX_DETECTION_RANGE,
    MIN_DETECTION_ANGLE, MAX_DETECTION_ANGLE, QUALITY_THRESHOLD,
)
from guerreDesTetes.aquisition.camera_worker import camera_worker
from guerreDesTetes.aquisition.lidar_worker import lidar_worker
from guerreDesTetes.aquisition.imu_worker import imu_worker
from guerreDesTetes.display import set_preview_frame, start_preview_server
from guerreDesTetes.modes import game_loop, selfie_phase

SELFIE_SAVE_DIR = Path("guerreDesTetes/selfies")
def main():
    parser = argparse.ArgumentParser()
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('-g', '--game', action='store_true', help="Lance directement la boucle de jeu")
    mode_group.add_argument('-s', '--selfie', action='store_true', help="Lance la phase de selfie")
    parser.add_argument('--displayflask', action='store_true',
                        help="Stream les fenêtres via Flask (/video) au lieu d'OpenCV imshow")
    args = parser.parse_args()

    flask_display = None
    if args.displayflask:
        flask_display = set_preview_frame
        start_preview_server()
        print("Flask stream disponible sur http://0.0.0.0:5000/video")

    print("Initialisation de la camera...")
    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    print("Initialisation du LiDAR...")
    lidar = LIDAR(
        PORT_LIDAR,
        quality_threshold=QUALITY_THRESHOLD,
        min_range=MIN_DETECTION_RANGE,
        max_range=MAX_DETECTION_RANGE,
        min_angle=MIN_DETECTION_ANGLE,
        max_angle=MAX_DETECTION_ANGLE,
    )
    lidar.start()
    lidar.warmup(3)

    print("Initialisation du bouton et de la LED...")
    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)

    state = {
        "latest_frame": None,
        "latest_points": [],
        "latest_imu": None,
    }
    lock = threading.Lock()
    stop_event = threading.Event()

    cam_thread = threading.Thread(
        target=camera_worker, args=(camera, state, lock, stop_event), daemon=True)
    lid_thread = threading.Thread(
        target=lidar_worker, args=(lidar, state, lock, stop_event), daemon=True)
    imu_thread = threading.Thread(
        target=imu_worker, args=(state, lock, stop_event), daemon=True)

    try:
        cam_thread.start()
        lid_thread.start()
        imu_thread.start()

        if args.selfie:
            selfie_phase(state, lock, button, led, SELFIE_SAVE_DIR, flask_display=flask_display)
        else:
            game_loop(state, lock, button, flask_display=flask_display)

    except KeyboardInterrupt:
        print("\nArret demande.")

    finally:
        stop_event.set()
        cam_thread.join(timeout=1.0)
        lid_thread.join(timeout=1.0)
        imu_thread.join(timeout=1.0)

        led.off()
        button.cleanup()
        led.cleanup()
        camera.stop()
        lidar.stop()
        print("Ressources liberees.")


if __name__ == "__main__":
    main()
