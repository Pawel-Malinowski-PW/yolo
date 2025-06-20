import cv2
import websocket
import ssl
import sys
import darknet
import numpy as np
import signal
import gc
import torch

config_path = "darknet/yolo3/yolov3-custom.cfg"
weights_path = "darknet/backup/yolov3-custom_final.weights"
data_path = "darknet/yolo3/obj.data"

net = darknet.load_net(config_path.encode(), weights_path.encode(), 0)
meta = darknet.load_meta(data_path.encode())

def array_to_image(arr):
    import cv2
    arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    arr = arr.transpose(2, 0, 1)
    c, h, w = arr.shape
    arr = arr.flatten() / 255.0
    data = (darknet.c_float * len(arr))()
    data[:] = arr
    im = darknet.IMAGE(w, h, c, data)
    return im

def detect_darknet_frame(net, meta, frame, thresh=0.5, hier_thresh=0.5, nms=0.45):
    im = array_to_image(frame)
    num = darknet.c_int(0)
    pnum = darknet.pointer(num)
    darknet.predict_image(net, im)
    dets = darknet.get_network_boxes(net, im.w, im.h, thresh, hier_thresh, None, 0, pnum)
    num = pnum[0]
    if nms:
        darknet.do_nms_obj(dets, num, meta.classes, nms)
    res = []
    for j in range(num):
        for i in range(meta.classes):
            if dets[j].prob[i] > 0:
                b = dets[j].bbox
                res.append((meta.names[i].decode(), dets[j].prob[i], (b.x, b.y, b.w, b.h)))
    darknet.free_detections(dets, num)
    return res

ws_url = "ws://localhost:8080"

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

            detections = detect_darknet_frame(net, meta, frame)
            for label, confidence, bbox in detections:
                x, y, w, h = map(int, bbox)
                x1, y1 = x - w // 2, y - h // 2
                x2, y2 = x + w // 2, y + h // 2
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(frame, f"{label} {confidence}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        

        _, buffer = cv2.imencode('.jpg', frame)
        ws.send(buffer.tobytes(), opcode=websocket.ABNF.OPCODE_BINARY)
    except Exception as e:
        print(f"błąd dla klatki: {e}")
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
    ws.send("script")

ws = websocket.WebSocketApp(
    ws_url,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)
ws.on_open = on_open

if __name__ == "__main__":
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

def cleanup_and_exit(signum, frame):
    global net, ws
    try:
        del net
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
