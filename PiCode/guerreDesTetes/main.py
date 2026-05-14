import argparse
import sys
import cv2
import time
import threading
import numpy as np
from pathlib import Path

from sensors.CAMERA import Camera
from sensors.LIDAR import LIDAR
from utils import Button, LED
from postprocessing.rotate_lidar_scans_180 import rotate_point_180_via_polar
from config import (
    PORT_BUTTON, PORT_LED,
    PORT_LIDAR,
    MIN_DETECTION_RANGE, MAX_DETECTION_RANGE,
    MIN_DETECTION_ANGLE, MAX_DETECTION_ANGLE, QUALITY_THRESHOLD,
)
from guerreDesTetes.capture import capture_face_sprite
from guerreDesTetes.aquisition.camera_worker import camera_worker
from guerreDesTetes.aquisition.lidar_worker import lidar_worker
from guerreDesTetes.aquisition.imu_worker import imu_worker
from guerreDesTetes.overlay import load_heads, overlay_png, viseur
from guerreDesTetes.gameUtils.game import Ennemi

SELFIE_SAVE_DIR = Path("guerreDesTetes/selfies")
MAP_WINDOW_SIZE = 500
MAP_MAX_RANGE = 3000  # mm — portée affichée sur la fenêtre Map

# def load_heads(size=(130,130), path="selfies/"):
# def overlay_png(frame,png,x,y):
# def viseur(frame):


# ---------------------------------------------------------------------------
# Rendu — fonctions issues de replay_multisensor.py
# ---------------------------------------------------------------------------

def render_lidar_frame(points, max_range=MAP_MAX_RANGE, window_size=MAP_WINDOW_SIZE, min_range=None):
    """Construit une image OpenCV représentant le nuage de points LiDAR."""
    scale = (window_size * 0.45) / max_range
    center = window_size // 2

    frame = np.zeros((window_size, window_size, 3), dtype=np.uint8)
    frame[center, :] = (40, 40, 40)
    frame[:, center] = (40, 40, 40)

    cv2.circle(frame, (center, center), int(max_range * scale), (80, 80, 80), 1)
    if min_range is not None and min_range > 0:
        cv2.circle(frame, (center, center), int(min_range * scale), (60, 60, 60), 1)

    cv2.drawMarker(frame, (center, center), (0, 0, 255),
                   markerType=cv2.MARKER_CROSS, markerSize=12, thickness=1)

    if points:
        pts = np.array(points, dtype=np.float32)
        px = (center + pts[:, 0] * scale).astype(int)
        py = (center - pts[:, 1] * scale).astype(int)
        valid = (px >= 0) & (px < window_size) & (py >= 0) & (py < window_size)
        frame[py[valid], px[valid]] = (255, 255, 255)

    return frame


def draw_text_block(frame, lines, origin=(10, 25), line_height=22, font_scale=0.55):
    """Ajoute des lignes de texte sur une image."""
    x, y = origin
    for i, line in enumerate(lines):
        cv2.putText(frame, str(line), (x, y + i * line_height),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1, cv2.LINE_AA)


_MAP_OVERLAY_SIZE = 160  # taille en px de la minimap incrustée en haut à droite

def _overlay_map(camera_frame, points):
    """Incrustation de la carte LiDAR en haut à droite du frame caméra."""
    size = _MAP_OVERLAY_SIZE
    mini = render_lidar_frame(points, max_range=MAP_MAX_RANGE, window_size=size,
                              min_range=MIN_DETECTION_RANGE)
    draw_text_block(mini, [f"{len(points)} pts"], font_scale=0.4)
    out = camera_frame.copy()
    _, w = out.shape[:2]
    out[0:size, w - size:w] = mini
    return out


# ---------------------------------------------------------------------------
# Phase 1 — Capture des selfies
# ---------------------------------------------------------------------------

def selfie_phase(state, lock, button, led, flask_display=None):
    """
    Boucle de capture et validation des selfies.
    Bouton physique : capture  |  'q' (ou 'q'+Entrée en mode Flask) : passer au jeu.
    Retourne le dernier sprite validé, ou None.
    """
    SELFIE_SAVE_DIR.mkdir(exist_ok=True)
    index = len(list(SELFIE_SAVE_DIR.glob("sprite_*.jpg")))
    sprite = None
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    draw_text_block(blank, ["Attente caméra..."])

    if flask_display is not None:
        print("=== Phase selfie (Flask) — Bouton: capturer | tapez 'q'+Entrée pour lancer le jeu ===")
    else:
        print("=== Phase selfie — Bouton: capturer | q: lancer le jeu (>=1 selfie) ===")

    while True:
        with lock:
            frame = state["latest_frame"].copy() if state["latest_frame"] is not None else blank.copy()

        display = frame.copy()
        draw_text_block(display, [
            f"Selfie #{index}",
            "BOUTON: capturer  |  q: lancer le jeu",
        ])

        if flask_display is not None:
            flask_display(display)
            time.sleep(0.033)
            # Vérification non-bloquante de stdin (Linux/Pi)
            try:
                import select
                if index > 0 and select.select([sys.stdin], [], [], 0)[0]:
                    if sys.stdin.readline().strip().lower() == 'q':
                        break
            except Exception:
                pass
        else:
            cv2.imshow("Selfie", display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') and index > 0:
                break

        if button.is_pressed():
            led.on()

            with lock:
                frame = state["latest_frame"].copy() if state["latest_frame"] is not None else blank.copy()

            cv2.imwrite(str(SELFIE_SAVE_DIR / f"selfie_{index:03d}.jpg"), frame)

            sprite = capture_face_sprite(frame)
            if sprite is not None:
                if flask_display is not None:
                    flask_display(sprite)
                    time.sleep(1.0)
                else:
                    cv2.imshow("Sprite", sprite)
                    cv2.waitKey(1000)
                conf = input("Sprite correct ? (y/n) : ").strip().lower()
                if conf == 'y':
                    sprite_path = str(SELFIE_SAVE_DIR / f"sprite_{index:03d}.jpg")
                    cv2.imwrite(sprite_path, sprite)
                    print(f"Sprite sauvegardé : {sprite_path}")
                    index += 1
                if flask_display is None:
                    cv2.destroyWindow("Sprite Capturé")
            else:
                print("[selfie] Aucun visage détecté, réessayez.")

            button.wait_for_release()
            led.off()
            time.sleep(0.2)

    if flask_display is None:
        cv2.destroyWindow("Selfie")
    return sprite


# ---------------------------------------------------------------------------
# Phase 2 — Boucle de jeu
# ---------------------------------------------------------------------------

def update_camera_window(frame, imu, show_window=True):
    """Prépare la vue Camera avec l'overlay IMU en bas de frame."""
    if imu is not None:
        ax, ay, az, gx, gy, gz = imu
        draw_text_block(frame, [
            f"Accel: ({ax:.2f}, {ay:.2f}, {az:.2f}) g",
            f"Gyro:  ({gx:.2f}, {gy:.2f}, {gz:.2f}) dps",
        ], origin=(10, frame.shape[0] - 55))

        # rajouter viseur sur frame
        frame = viseur(frame)
    if show_window:
        cv2.imshow("Camera", frame)
    return frame


def update_map_window(points, show_window=True):
    """Prépare la fenêtre Map avec le dernier scan LiDAR."""
    map_frame = render_lidar_frame(points, max_range=MAP_MAX_RANGE,
                                   window_size=MAP_WINDOW_SIZE,
                                   min_range=MIN_DETECTION_RANGE)
    draw_text_block(map_frame, [f"LiDAR — {len(points)} pts"])
    if show_window:
        cv2.imshow("Map", map_frame)
    return map_frame


def print_imu(imu, last_print_time, interval=0.5):
    """Affiche les données IMU en console à intervalle régulier. Retourne le nouveau timestamp."""
    now = time.time()
    if imu is not None and now - last_print_time >= interval:
        ax, ay, az, gx, gy, gz = imu
        print(f"[IMU] accel=({ax:.3f}, {ay:.3f}, {az:.3f}) g | "
              f"gyro=({gx:.3f}, {gy:.3f}, {gz:.3f}) dps")
        return now
    return last_print_time


def game_loop(state, lock, flask_display=None):
    """
    Boucle principale du jeu — appelle une fonction par tâche à chaque frame :
      - update_camera_window : flux caméra (ennemis AR a ajouter plus tard)
      - update_map_window    : vue LiDAR top-down (ennemis en rouge plus tard)
      - print_imu            : print console (debugg, à retirer plus tard) (a retirer de suite)
    'q' pour quitter.
    """
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    draw_text_block(blank, ["Attente camera..."])

    if flask_display is not None:
        print("=== Boucle de jeu demarree (Flask) — Ctrl+C pour quitter ===")
    else:
        print("=== Boucle de jeu demarree — 'q' pour quitter ===")

    while True:
        with lock:
            frame = state["latest_frame"].copy() if state["latest_frame"] is not None else blank.copy()
            points = list(state["latest_points"])
            imu = state["latest_imu"]

        frame = ennemi.afficher(frame)

        if flask_display is not None:
            camera_frame = update_camera_window(frame, imu, show_window=False)
            flask_display(_overlay_map(camera_frame, points))
            try:
                import select
                if select.select([sys.stdin], [], [], 0)[0]:
                    if sys.stdin.readline().strip().lower() == 'q':
                        break
            except Exception:
                pass
            time.sleep(0.033)
        else:
            update_camera_window(frame, imu)
            update_map_window(points)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    cv2.destroyAllWindows()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--displayflask', action='store_true',
                        help="Stream les fenêtres via Flask (/video) au lieu d'OpenCV imshow")
    args = parser.parse_args()

    flask_display = None
    if args.displayflask:
        from guerreDesTetes.display import set_preview_frame
        flask_display = set_preview_frame
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

        selfie_phase(state, lock, button, led, flask_display=flask_display)
        game_loop(state, lock, flask_display=flask_display)

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
    ennemi = Ennemi("test", angle=45, profondeur=1000, z=0, vie=3, sprite=load_heads()[0])
    main()
