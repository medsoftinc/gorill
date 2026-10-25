import os
import numpy as np
import rclpy
from PIL import Image as PilImage
from sensor_msgs.msg import Image

KLASOR = os.path.expanduser("~/gorill/data/frames")
os.makedirs(KLASOR, exist_ok=True)

rclpy.init()
node = rclpy.create_node("kamera_kayit")
sayac = 0

def goruntu_geldi(msg):
    global sayac
    sayac += 1
    if sayac % 10 != 0:
        return
    kanal = 4 if msg.encoding in ("rgba8", "bgra8") else 3
    kare = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.step)[:, :msg.width * kanal]
    kare = kare.reshape(msg.height, msg.width, kanal)[:, :, :3]
    if msg.encoding.startswith("bgr"):
        kare = kare[:, :, ::-1]
    dosya = os.path.join(KLASOR, f"kare_{sayac:05d}.png")
    PilImage.fromarray(kare).save(dosya)
    print("Kaydedildi:", dosya)

node.create_subscription(Image, "/camera/image", goruntu_geldi, 10)
rclpy.spin(node)
