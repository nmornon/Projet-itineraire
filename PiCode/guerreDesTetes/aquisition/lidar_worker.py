import time
from postprocessing.rotate_lidar_scans_180 import rotate_point_180_via_polar

def lidar_worker(lidar, state, lock, stop_event):
    """Thread LiDAR : stocke les derniers points dans state['latest_points']."""
    while not stop_event.is_set():
        try:
            _timestamp, _measures, points = lidar.read_scan()
            points = [rotate_point_180_via_polar(point[0], point[1]) for point in points]
            with lock:
                state["latest_points"] = points
        except Exception as e:
            print(f"[lidar] Erreur : {e}")
        time.sleep(0.01)
