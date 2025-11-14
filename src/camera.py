import cv2
import numpy as np

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

    def __enter__(self):
            if not self.cap.isOpened():
                print("[Camera] Error: Camera source not opened.")
                return None 
            return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("[Camera] Releasing capture...")
        self.release()

    def read(self) -> tuple[bool, np.ndarray]:
            try:
                ret, frame = self.cap.read()
                if ret:
                    self.frame_idx += 1 
                return ret, frame
            except Exception as e:
                print(f"[Camera] Read error: {e}")
                return False, None

    def release(self) -> None:
        try:
            self.cap.release()
        except Exception as e:
            print(f"[Camera] Release error: {e}")
        
    def grab(self) -> bool:
        try:
            return self.cap.grab()
        except Exception as e:
            print(f"[Camera] Grab error: {e}")
            return False

    def should_infer(self) -> bool:
        return self.frame_idx % self.every_n == 0

    def isOpened(self) -> bool:
        """ เช็คว่ากล้องเปิดอยู่จริงไหม """
        return self.cap.isOpened()

    @property
    def width(self) -> int:
        """ ดึงค่าความกว้างจริงของ frame """
        return int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self) -> int:
        """ ดึงค่าความสูงจริงของ frame """
        return int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    @property
    def fps(self) -> float:
        """ ดึงค่า FPS จริงของ video/camera """
        return self.cap.get(cv2.CAP_PROP_FPS)



if __name__ == "__main__":
    print("[INFO] VideoSource")
    with VideoSource(0, every_n=1) as cam:
        while True:
            ok, frame = cam.read()
            if not ok:
                print("Camera read failed")
                break
            
            if cam.should_infer():
                print(f"Frame size: {cam.fps}")
                cv2.imshow("Detection", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break