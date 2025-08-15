import cv2

def draw_alerts(frame, alerts):
    for d in alerts:
        x1, y1, x2, y2 = d["bbox"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 1)
        cv2.putText(frame, d["cls"], (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)


