import time


def camera_worker(camera, state, lock, stop_event):
    """Thread caméra : stocke la dernière frame dans state['latest_frame']."""
    while not stop_event.is_set():
        try:
            frame = camera.capture_frame()
            with lock:
                state["latest_frame"] = frame
        except Exception as e:
            print(f"[camera] Erreur : {e}")
        time.sleep(0.01)
