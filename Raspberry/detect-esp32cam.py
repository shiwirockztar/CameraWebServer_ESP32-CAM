import argparse
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

def parse_args():
    parser = argparse.ArgumentParser(description="Detect objects using YOLO model on ESP32-CAM stream")
    parser.add_argument("--url", type=str, required=True, help="URL of the ESP32-CAM stream (e.g., http://IP-ASIGNADA-ARDUINO/cam-hi.jpg)")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Path to the YOLO model file")
    parser.add_argument("--conf", type=float, default=0.35, help="Umbral de confianza para las detecciones")
    parser.add_argument("--save", action="store_true", help="Guardar el video con las detecciones en output.mp4")   
    parser.add_argument("--show", action="store_true", help="Show the video stream with detections")
    parser.add_argument("--max-w", type=int, default=640, help="Redimensionar ancho máximo del frame (0 para no redimensionar)")
    parser.add_argument("--reconnect", type=int, default=3, help="Time to wait before reconnecting (in seconds)")
    return parser.parse_args()

def open_capture(url:str):
    cap=cv2.VideoCapture(url,cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE,1)
    return cap

def main():
    args = parse_args()
    model = YOLO(args.model)

    cap = open_capture(args.url)
    if not cap.isOpened():
        print("Error: Unable to open video stream.")
        return

    #guardado opcional
    writer = None
    if args.save:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter("output.mp4", fourcc, 20, (640, 480)) # Ajusta el primer frame tamaño según sea necesario

    prev_time = time.time()
    fps = 0.0
    reconnect_left = args.reconnect

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            print("Warning: Unable to read frame from stream. [frame nulo. intentando reconectar   ...]")
            cap.release()
            time.sleep(0.7)
            cap = open_capture(args.url)
            if not cap.isOpened():
                reconnect_left -= 1
                if reconnect_left <= 0:
                    print("Error: Unable to reconnect to video stream.")
                    break
                continue
            reconnect_left = args.reconnect
            continue
        
        if args.max_w > 0 and frame.shape[1] > args.max_w:
            h = int(frame.shape[0] * args.max_w / frame.shape[1])
            frame = cv2.resize(frame, (args.max_w, h),interpolation=cv2.INTER_AREA)

        # Inferencia YOLO
        results = model.predict(source=frame, conf=args.conf, verbose=False)
        annotated = frame.copy()
        
        # Dibujar detecciones
        for r in results:
            if r.boxes is not None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                x1, y1, x2, y2 = xyxy.tolist()

                label = f"{model.names.get(cls_id, cls_id)} {conf:.2f}"
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated,(x1, y1 - th - 6),(x1 + tw + 4 , y1),(0, 255, 0),-1)
                cv2.putText(annotated, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        # Fps simple (suavizado)
        now = time.time()
        fps =fps * 0.9 + (1.0 / max(1e-6, now - prev_time)) * 0.1
        prev_time = now
        cv2.putText(annotated, f"FPS: {fps:.1f}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # inicializar writer con tamaño correcto del frame
        if writer is not None and not writer.isOpened():
            h, w = annotated.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer.open("output.mp4", fourcc, 20.0, (w, h))

        if writer is not None:
            writer.write(annotated)

        if args.show:
            cv2.imshow("ESP32-CAM Detection + Yolov8", annotated)
            # Salir con ESC o "q"
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):  # ESC key or "q"
                break
    if writer is not None:
        writer.release()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()