import sys
import time
import random

import cv2
import numpy as np

from guerreDesTetes.capture import capture_face_sprite
from guerreDesTetes.gameUtils.game import Ennemi
from guerreDesTetes.gameUtils.imu_position_tracking import update_imu_position_tracking
from guerreDesTetes.gameUtils.projectile import Projectile
from guerreDesTetes.overlay import load_heads, viseur
from guerreDesTetes.rendering import MAP_MAX_RANGE, create_map_window, draw_text_block, overlay_map

ENEMY_SPAWN_INTERVAL_S = 2.5
ENEMY_MAX_COUNT = 8
ENEMY_SPAWN_ANGLE_MIN = -45
ENEMY_SPAWN_ANGLE_MAX = 45
ENEMY_SPAWN_RANGE_MIN = 900
ENEMY_SPAWN_RANGE_MAX = 2500
PROJECTILE_COOLDOWN_S = 0.25


def selfie_phase(state, lock, button, led, selfie_save_dir, flask_display=None):
    """
    Boucle de capture et validation des selfies.
    Bouton physique : capture  |  'q' (ou 'q'+Entrée en mode Flask) : passer au jeu.
    Retourne le dernier sprite validé, ou None.
    """
    selfie_save_dir.mkdir(exist_ok=True)
    index = len(list(selfie_save_dir.glob("sprite_*.png")))
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

            cv2.imwrite(str(selfie_save_dir / f"selfie_{index:03d}.jpg"), frame)

            sprite = capture_face_sprite(frame)
            if sprite is not None:
                preview_sprite = sprite[:, :, :3] if sprite.ndim == 3 and sprite.shape[2] == 4 else sprite
                if flask_display is not None:
                    flask_display(preview_sprite)
                    time.sleep(1.0)
                else:
                    cv2.imshow("Sprite", preview_sprite)
                    cv2.waitKey(1000)
                conf = input("Sprite correct ? (y/n) : ").strip().lower()
                if conf == 'y':
                    sprite_path = str(selfie_save_dir / f"sprite_{index:03d}.png")
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


def update_camera_window(frame, imu, show_window=True):
    """Prépare la vue Camera avec l'overlay IMU en bas de frame."""
    if imu is not None:
        ax, ay, az, gx, gy, gz = imu
        draw_text_block(frame, [
            f"Accel: ({ax:.2f}, {ay:.2f}, {az:.2f}) g",
            f"Gyro:  ({gx:.2f}, {gy:.2f}, {gz:.2f}) dps",
        ], origin=(10, frame.shape[0] - 55))
        frame = viseur(frame)
    if show_window:
        cv2.imshow("Camera", frame)
    return frame


def print_imu(imu, last_print_time, interval=0.5):
    """Affiche les données IMU en console à intervalle régulier. Retourne le nouveau timestamp."""
    now = time.time()
    if imu is not None and now - last_print_time >= interval:
        ax, ay, az, gx, gy, gz = imu
        print(f"[IMU] accel=({ax:.3f}, {ay:.3f}, {az:.3f}) g | "
              f"gyro=({gx:.3f}, {gy:.3f}, {gz:.3f}) dps")
        return now
    return last_print_time


def create_projectile(projectiles):
    """Crée un projectile à partir d'une position et d'un sprite."""
    projectile = Projectile("Projectile")
    projectiles.append(projectile)


def update_projectiles(projectiles, frame):
    """Met à jour la position et l'animation de chaque projectile."""
    for proj in projectiles[:]:
        if proj.getPosition()["r"] > MAP_MAX_RANGE:
            projectiles.remove(proj)
            continue
        proj.move(100)
        proj.updateFrame()
        proj.render_image(frame)


def spawn_enemy_if_needed(ennemis, heads, next_spawn_ts, now_ts=None):
    """Ajoute périodiquement un ennemi dans le cône frontal de la caméra."""
    if now_ts is None:
        now_ts = time.monotonic()

    if len(ennemis) >= ENEMY_MAX_COUNT or now_ts < next_spawn_ts:
        return next_spawn_ts

    sprite = random.choice(heads) if heads else None
    ennemi = Ennemi(
        f"Ennemi{len(ennemis) + 1}",
        angle=random.uniform(ENEMY_SPAWN_ANGLE_MIN, ENEMY_SPAWN_ANGLE_MAX),
        profondeur=random.uniform(ENEMY_SPAWN_RANGE_MIN, ENEMY_SPAWN_RANGE_MAX),
        z=random.uniform(-5, 5),
        sprites=[sprite],
    )
    ennemis.append(ennemi)
    return now_ts + ENEMY_SPAWN_INTERVAL_S


def game_loop(state, lock, button, flask_display=None):
    """
    Boucle principale du jeu — appelle une fonction par tâche à chaque frame.
    """
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    draw_text_block(blank, ["Attente camera..."])

    heads = load_heads()
    ennemis = []
    projectiles = []
    next_enemy_spawn_ts = time.monotonic() + 0.5
    next_projectile_ts = 0.0

    if flask_display is not None:
        print("=== Boucle de jeu demarree (Flask) — Ctrl+C pour quitter ===")
    else:
        print("=== Boucle de jeu demarree — 'q' pour quitter ===")

    while True:
        now_ts = time.monotonic()

        with lock:
            frame = state["latest_frame"].copy() if state["latest_frame"] is not None else blank.copy()
            points = list(state["latest_points"])
            imu = state["latest_imu"]

        if imu is not None:
            update_imu_position_tracking(*imu)

        next_enemy_spawn_ts = spawn_enemy_if_needed(
            ennemis,
            heads,
            next_enemy_spawn_ts,
            now_ts=now_ts,
        )

        minimap = create_map_window(points, show_window=flask_display is None)

        for ennemi in ennemis:
            frame = ennemi.render(frame, minimap)

        if button.is_pressed() and now_ts >= next_projectile_ts:
            create_projectile(projectiles)
            next_projectile_ts = now_ts + PROJECTILE_COOLDOWN_S
        update_projectiles(projectiles, frame)

        if flask_display is not None:
            camera_frame = update_camera_window(frame, imu, show_window=False)
            flask_display(overlay_map(camera_frame, minimap))
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
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    cv2.destroyAllWindows()