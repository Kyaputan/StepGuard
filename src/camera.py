import cv2

class VideoSource:
    def __init__(self, src=0, width=None, height=None , frame_idx=0 , every_n=1 , backend=cv2.CAP_ANY):
        self.cap = cv2.VideoCapture(src , backend)
        self.frame_idx = frame_idx
        self.every_n = every_n
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        if width:  
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        if height: 
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self):
        try:
            return self.cap.read()
        except Exception as e:
            print(f"[Camera] Read error: {e}")
            return False, None

    def release(self):
        try:
            self.cap.release()
        except Exception as e:
            print(f"[Camera] Release error: {e}")
        
    def grab(self):
        try:
            return self.cap.grab()
        except Exception as e:
            print(f"[Camera] Grab error: {e}")
            return False

    def should_infer(self):
        return self.frame_idx % self.every_n == 0
    
if __name__ == "__main__":
    print("[INFO] VideoSource")
    cam = VideoSource(0, every_n=1)
    while True:
        ok, frame = cam.read()
        if not ok:
            print("Camera read failed")
            break
        cv2.imshow("Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        cam.frame_idx += 1