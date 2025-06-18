# YOLO Web Detection

Projekt umożliwia przesyłanie obrazu z kamery na serwer, detekcję obiektów (YOLOv3/YOLOv5) i podgląd wyników przez przeglądarkę.

## Struktura katalogów

- `serwerek/` – główny backend (Node.js + WebSocket + Python)
    - `server.js` – serwer HTTP/WebSocket
    - `script.py` – detekcja YOLOv3 (Darknet)
    - `script2.py` – detekcja YOLOv5 (PyTorch)
    - `index.html`, `stream.html` – frontend

## Czego nie ma

1. **Zależności Node.js:**  
   Wykonaj polecenie w katalogu `serwerek`:

    ```bash
    npm install
    ```

2. **Wymagane pakiety Pythona:**  
   W pliku `requirements.txt` znajdują się pakiety:
   - opencv-python
   - websocket-client
   - numpy
   - torch
   - yolov5

   Można je zainstalować poleceniem:

    ```bash
    pip install -r requirements.txt
    ```

3. **Klonowanie repozytorium Darknet do folderu `serwerek/darknet` z obsługą Pythona:**

    ```bash
    cd serwerek
    git clone https://github.com/AlexeyAB/darknet.git
    cd darknet
    # Włącz obsługę Pythona w Makefile (PYTHON=1) i skompiluj:
    sed -i 's/^PYTHON=0/PYTHON=1/' Makefile
    make
    ```
    Wymagane jest dodanie ścieżki `darknet/python/darknet.py` do modułów Pythona (`PYTHONPATH` lub dowiązanie symboliczne).
    Jeśli chcesz obsługiwać detekcję na karcie graficznej, postępuj zgodnie z poradnikiem na stronie:  
    https://pjreddie.com/darknet/yolo/

## Uruchamianie

W katalogu `serwerek` wykonaj polecenie:

```bash
node server.js
```

## Uwaga

- Projekt korzysta z reverse proxy HTTPS do publicznego adresu. Adres ten jest hostowany na zewnętrznym serwerze i nie jest ogólnodostępny. Możesz użyć swojego serwera HTTPS i podać jego adres w pliku `stream.html`.  
  W przeciwnym wypadku projekt wymaga zmiany `http` na `https`, a wraz z nim `ws` na `wss` w plikach `server.js`, `script.py`, `script2.py` oraz ustawienia adresu `wss` w pliku `stream.html` na taki sam jak w plikach `script.py` i `script2.py`.
- Pliki wag YOLO (`.pt`, `.weights`) nie są przechowywane w repozytorium – pobierz je osobno z repozytorium Darknet dla YOLOv3 lub Ultralytics dla YOLOv5.

## Autor

Paweł Malinowski  
Wydział Elektryczny  
Politechnika Warszawska

---
