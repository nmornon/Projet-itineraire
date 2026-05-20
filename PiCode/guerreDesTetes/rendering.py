import cv2
import numpy as np

from config.parameters import CAMERA_FOV_DEGREES, MIN_DETECTION_RANGE

MAP_WINDOW_SIZE = 500
MAP_MAX_RANGE = 3000  # mm
MAP_OVERLAY_SIZE = 200
MINIMAP_POINT_RADIUS = 4
MINIMAP_CENTER_COLOR = (255, 0, 0)
MINIMAP_FOV_COLOR = (255, 0, 0)


def draw_text_block(frame, lines, origin=(10, 25), line_height=22, font_scale=0.55):
    """Ajoute des lignes de texte sur une image."""
    x, y = origin
    for i, line in enumerate(lines):
        cv2.putText(frame, str(line), (x, y + i * line_height),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1, cv2.LINE_AA)


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

    cv2.drawMarker(frame, (center, center), MINIMAP_CENTER_COLOR,
                   markerType=cv2.MARKER_CROSS, markerSize=16, thickness=2)
    cv2.circle(frame, (center, center), 5, MINIMAP_CENTER_COLOR, -1)

    half_fov_rad = np.deg2rad(CAMERA_FOV_DEGREES / 2.0)
    fov_length = int(max_range * scale)
    for sign in (-1, 1):
        angle = sign * half_fov_rad
        end_x = int(center + np.sin(angle) * fov_length)
        end_y = int(center - np.cos(angle) * fov_length)
        cv2.line(frame, (center, center), (end_x, end_y), MINIMAP_FOV_COLOR, 2)

    if points:
        pts = np.array(points, dtype=np.float32)
        px = (center + pts[:, 0] * scale).astype(int)
        py = (center - pts[:, 1] * scale).astype(int)
        valid = (px >= 0) & (px < window_size) & (py >= 0) & (py < window_size)
        for x, y in zip(px[valid], py[valid]):
            cv2.circle(frame, (int(x), int(y)), MINIMAP_POINT_RADIUS, (255, 255, 255), -1)

    return frame


def overlay_map(camera_frame, minimap):
    """Incrustation de la carte LiDAR en haut à droite du frame caméra."""
    size = MAP_OVERLAY_SIZE
    out = camera_frame.copy()
    _, w = out.shape[:2]
    if minimap.shape[:2] != (size, size):
        minimap = cv2.resize(minimap, (size, size))
    out[0:size, w - size:w] = minimap
    return out


def create_map_window(points, show_window=True):
    """Prépare la fenêtre Map avec le dernier scan LiDAR."""
    map_frame = render_lidar_frame(points, max_range=MAP_MAX_RANGE,
                                   window_size=MAP_WINDOW_SIZE,
                                   min_range=MIN_DETECTION_RANGE)
    if show_window:
        cv2.imshow("Map", map_frame)
    return map_frame