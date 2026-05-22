import cv2
import numpy as np

def resizeimg(im:np.ndarray, new_shape=(640, 640), color=(26, 26, 26)) -> np.ndarray:
    """
    ทำการ resize image โดยไม่เสียสัดส่วน
    """
    h, w = im.shape[:2]
    scale = min(new_shape[0] / h, new_shape[1] / w)
    nh, nw = int(h * scale), int(w * scale)
    resized = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_AREA)
    new_im = np.full((new_shape[1], new_shape[0], 3), color, dtype=np.uint8)
    top: int  = (new_shape[1] - nh) // 2
    left: int = (new_shape[0] - nw) // 2
    new_im[top:top + nh, left:left + nw] = resized
    return new_im
