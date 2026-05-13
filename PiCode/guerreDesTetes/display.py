import cv2
import numpy as np
from flask import Flask, Response, redirect
import threading
import time

app = Flask(__name__)
_current_frame = None

def set_preview_frame(frame):
    global _current_frame
    _current_frame = frame

def _generate():
    while True:
        if _current_frame is None:
            continue
        _, jpeg = cv2.imencode('.jpg', _current_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

@app.route('/')
def index():
    return redirect('/video')

@app.route('/video')
def video():
    return Response(_generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Lance Flask dans un thread séparé pour ne pas bloquer ton code
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()

if __name__ == '__main__':
    print("Stream dispo sur http://0.0.0.0:5000/video")
    i = 0
    while True:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, f"Frame {i}", (50, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        set_preview_frame(frame)
        i += 1
        time.sleep(0.033)

