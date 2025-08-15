import cv2

class VideoSource:
    def __init__(self, src=0, width=None, height=None , frame_idx=0 , every_n=1):
        self.cap = cv2.VideoCapture(src)
        self.frame_idx = frame_idx
        self.every_n = every_n
        if width:  self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        if height: self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self):
        return self.cap.read()

    def release(self):
        self.cap.release()

    def should_infer(self):
        return self.frame_idx % self.every_n == 0
