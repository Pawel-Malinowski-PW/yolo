import cv2
import websocket
import numpy as np
import ssl

# YOLOv3-tiny konfiguracja i wagi
yolo_cfg = "yolov3-tiny.cfg"
yolo_weights = "yolov3-tiny.weights"
# Wczytanie modelu YOLOv3-tiny
yolo_net = cv2.dnn.readNetFromDarknet(yolo_cfg, yolo_weights)
yolo_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
yolo_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
# Pobranie nazw warstw
layer_names = yolo_net.getLayerNames()
# Pobranie nazw warstw wyjściowych
try:
    output_layers = [layer_names[i - 1] for i in yolo_net.getUnconnectedOutLayers().flatten()]
except AttributeError:
    # Dla starszych wersji OpenCV
    output_layers = [layer_names[i[0] - 1] for i in yolo_net.getUnconnectedOutLayers()]

# Wczytanie nazw klas
with open("coco.names", "r") as f:
    class_names = [line.strip() for line in f.readlines()]

# Adres serwera WebSocket 
ws_url = "wss://172.29.192.121:8080"

# Funkcja obsługująca wiadomości przychodzące
def on_message(ws, message):
    try:
        # Konwersja odebranych danych na obraz
        np_arr = np.frombuffer(message, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is not None:
            # Przygotowanie klatki do YOLO
            blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), swapRB=True, crop=False)
            # Ustawienie wejścia dla modelu
            yolo_net.setInput(blob)
            # Wykonanie detekcji
            detections = yolo_net.forward(output_layers)

            # Rysowanie prostokątów ograniczających na klatce
            for detection in detections:
                for obj in detection:
                    scores = obj[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    if confidence > 0.5:  # próg pewności
                        # Obliczanie współrzędnych prostokąta ograniczającego
                        center_x, center_y, width, height = (obj[0:4] * np.array([frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]])).astype("int")
                        x = int(center_x - width / 2)
                        y = int(center_y - height / 2)
                        cv2.rectangle(frame, (x, y), (x + int(width), y + int(height)), (0, 255, 0), 2)
                        label = f"{class_names[class_id]}: {confidence:.2f}"  # etykieta z nazwą klasy i pewnością
                        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Kodowanie przetworzonego obrazu do formatu JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Wysyłanie przetworzonej klatki z powrotem do serwera
            ws.send(frame_bytes, opcode=websocket.ABNF.OPCODE_BINARY)
    except Exception as e:
        print(f"błąd dla klatki: {e}")

# Funkcja obsługująca błędy
def on_error(ws, error):
    print(f"WebSocket błąd: {error}")

# Funkcja obsługująca zamknięcie połączenia
def on_close(ws, close_status_code, close_msg):
    print("WebSocket zamknięty")

# Funkcja obsługująca otwarcie połączenia
def on_open(ws):
    print("WebSocket połączony")
    ws.send("script")  # Wysyłanie identyfikatora klienta

# Konfiguracja WebSocket z ignorowaniem weryfikacji certyfikatu
ws = websocket.WebSocketApp(
    ws_url,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)
ws.on_open = on_open

# Uruchom klienta WebSocket z niestandardowym SSL
if __name__ == "__main__":
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
