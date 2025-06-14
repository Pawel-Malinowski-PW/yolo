import cv2
import numpy as np
import websocket
import ssl
import torch
from yolov5 import YOLOv5
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Załaduj model YOLOv5 (możesz zmienić na yolov5s.pt, yolov5m.pt, itp.)
model_path = '/home/malinop4/Dokumenty/projekty/yolo/serwerek/best.pt'
if torch.cuda.is_available():
    device = '0'  # GPU numer 0
else:
    device = 'cpu'
model = YOLOv5(model_path, device)

ws_url = "wss://localhost:8080"

import threading
from collections import deque

frame_queue = deque(maxlen=3)
queue_lock = threading.Lock()
processing = False

def on_message(ws, message):
    global frame_queue
    with queue_lock:
        frame_queue.append(message)
    start_processing(ws)

def start_processing(ws):
    global processing
    with queue_lock:
        if processing or not frame_queue:
            return
        processing = True
        frame_data = frame_queue.popleft()
    threading.Thread(target=process_frame, args=(ws, frame_data)).start()

def process_frame(ws, frame_data):
    global processing
    try:
        np_arr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is not None:
            results = model.predict(frame)
            detections = results.xyxy[0].cpu().numpy()
            for *xyxy, conf, cls in detections:
                label = model.model.names[int(cls)]
                x1, y1, x2, y2 = map(int, xyxy)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
            _, buffer = cv2.imencode('.jpg', frame)
            ws.send(buffer.tobytes(), opcode=websocket.ABNF.OPCODE_BINARY)
    except Exception as e:
        print(f"Błąd dla klatki: {e}")
    finally:
        global frame_queue
        with queue_lock:
            if frame_queue:
                next_frame = frame_queue.popleft()
                threading.Thread(target=process_frame, args=(ws, next_frame)).start()
            else:
                processing = False

def on_error(ws, error):
    print(f"WebSocket błąd: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket zamknięty")

def on_open(ws):
    print("WebSocket połączony")
    ws.send("script2")  # Wysyłanie identyfikatora klienta

ws = websocket.WebSocketApp(
    ws_url,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)
ws.on_open = on_open

import signal
import sys
import gc

def cleanup_and_exit(signum, frame):
    global model, ws
    try:
        del model
    except Exception:
        pass
    gc.collect()
    torch.cuda.empty_cache()
    try:
        ws.keep_running = False
        ws.close()
    except Exception:
        pass
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup_and_exit)
signal.signal(signal.SIGINT, cleanup_and_exit)

if __name__ == "__main__":
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})