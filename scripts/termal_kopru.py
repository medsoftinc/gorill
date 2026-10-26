# Desk kit bridge: MLX90640 frames from the Arduino (UDP 5006, 2 packets per frame) -> ROS 2 /thermal/raw
# Same format as the simulated thermal camera (mono16, kelvin x 100), so the live panel shows either one.
import socket, struct
import numpy as np
import rclpy
from sensor_msgs.msg import Image

W, H, YARIM = 32, 24, 32 * 24 // 2
rclpy.init()
node = rclpy.create_node("termal_kopru")
pub = node.create_publisher(Image, "/thermal/raw", 10)
soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
soket.bind(("0.0.0.0", 5006))
soket.settimeout(0.1)
parcalar = {}

def oku():
    try:
        veri = soket.recv(2048)
    except socket.timeout:
        return
    if len(veri) != 4 + YARIM * 2 or veri[:2] != b"TH":
        return
    kare_no, parca = veri[2], veri[3]
    parcalar[(kare_no, parca)] = np.frombuffer(veri[4:], "<i2")
    if (kare_no, 0) in parcalar and (kare_no, 1) in parcalar:
        santigrat = np.concatenate([parcalar.pop((kare_no, 0)), parcalar.pop((kare_no, 1))]) / 100.0
        kelvin100 = np.clip((santigrat + 273.15) * 100, 0, 65535).astype(np.uint16).reshape(H, W)
        msg = Image(height=H, width=W, encoding="mono16", step=W * 2, data=kelvin100.tobytes())
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = "mlx90640"
        pub.publish(msg)
    for k in [k for k in parcalar if (kare_no - k[0]) % 256 > 3]:   # drop stale halves
        parcalar.pop(k)

node.create_timer(0.01, oku)
print("Listening for MLX90640 frames on UDP 5006")
rclpy.spin(node)
