import os

import cv2
from ultralytics import YOLO

USERNAME = os.environ["CAMERA_USERNAME"]
PASSWORD = os.environ["CAMERA_PASSWORD"]
IP = os.environ.get("CAMERA_IP", "192.168.100.115")

rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@{IP}:554/cam/realmonitor?channel=2&subtype=0"

print("Conectando...")

cap = cv2.VideoCapture(rtsp_url)
model = YOLO("yolo11n.pt")

if not cap.isOpened():
    raise RuntimeError("No pude abrir el stream RTSP")

while True:
    ok, frame = cap.read()

    if not ok:
        print("No pude leer frame")
        break

    results = model(frame)

    annotated = results[0].plot()

    cv2.imshow("YOLO", annotated)

    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
