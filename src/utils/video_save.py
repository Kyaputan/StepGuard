import cv2
import time
import random

def save_video_from_rtsp(rtsp_url, output_path, duration=10):
    """
    บันทึกวิดิโอจาก RTSP stream โดยใช้ OpenCV และบันทึกในโฟลเดอร์ที่กำหนด

    Args:
        rtsp_url (str): URL ของ RTSP stream
        output_path (str): เส้นทางไฟล์สำหรับบันทึกวิดิโอ
        duration (int): ระยะเวลาในการบันทึก (วินาที), ค่าเริ่มต้น 10 วินาที
    """
    # เปิด RTSP stream
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print("ไม่สามารถเปิด RTSP stream ได้")
        return False

    # รับคุณสมบัติของเฟรม
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # ตั้งค่า FPS ค่าเริ่มต้นถ้าไม่ได้รับ
    if fps == 0 or fps is None:
        fps = 15.0
        
    # สร้าง VideoWriter สำหรับบันทึกวิดิโอ
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # ใช้ XVID สำหรับ AVI
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    if not out.isOpened():
        print("ไม่สามารถสร้างไฟล์วิดิโอได้")
        cap.release()
        return False

    print(f"เริ่มบันทึกวิดิโอจาก {rtsp_url} เป็นเวลา {duration} วินาที")
    print(f"ขนาดเฟรม: {width}x{height}, FPS: {fps}")

    start_time = time.time()

    try:
        while time.time() - start_time < duration:
            ret, frame = cap.read()
            if not ret:
                print("ไม่สามารถอ่านเฟรมได้")
                break

            out.write(frame)

        print(f"บันทึกวิดิโอเสร็จสิ้น: {output_path}")

    except KeyboardInterrupt:
        print("หยุดบันทึกวิดิโอ")

    finally:
        # ปิดทรัพยากร
        cap.release()
        out.release()
        cv2.destroyAllWindows()

    return True

if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    rtsp_url = "rtsp://Rachata:12345678@192.168.1.102:554/stream1"
    uid = random.randint(1, 100000)
    output_path = "src/utils/save/recorded_{}.avi".format(uid)
    save_video_from_rtsp(rtsp_url, output_path, duration=120)  # บันทึก 30 วินาที