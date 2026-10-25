# ROS 2 hot-spot detection node: /camera/image -> YOLO (OpenVINO) -> /detections + /camera/annotated,
# each detection logged with the drone position and the estimated ground position of the fault.
import csv, math, os, time
import cv2
import numpy as np
import rclpy
import yaml
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose
from px4_msgs.msg import VehicleOdometry
from ultralytics import YOLO

KOK = os.path.expanduser("~/gorill")
MODEL = os.environ.get("MODEL", f"{KOK}/models/sunhawk/weights/best_openvino_model")
site = yaml.safe_load(open(f"{KOK}/config/site.yaml"))
TAN = math.tan(site["camera"]["hfov_rad"] / 2)
PANEL_Z = site["rows"]["top_height"] - 0.5   # approx. height of the panel surface centre
GUVEN = 0.5                                  # minimum confidence

os.makedirs(f"{KOK}/data/detections", exist_ok=True)
csv_dosya = open(f"{KOK}/data/detections/detections.csv", "a", newline="")
yazici = csv.writer(csv_dosya)

rclpy.init()
node = rclpy.create_node("tespit_dugumu")
model = YOLO(MODEL, task="detect")
tespit_pub = node.create_publisher(Detection2DArray, "/detections", 10)
resim_pub = node.create_publisher(Image, "/camera/annotated", 10)
konum, yaw, son = None, 0.0, 0.0

def odometri(msg):
    global konum, yaw
    konum = [float(v) for v in msg.position]
    w, x, y, z = msg.q
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))

def yer_konumu(u, v, W, H):
    # pixel -> ground (north, east): image up = drone forward, image right = drone right
    yukseklik = -konum[2] - PANEL_Z
    metre_px = 2 * yukseklik * TAN / W
    ileri, sag = (H / 2 - v) * metre_px, (u - W / 2) * metre_px
    return (konum[0] + ileri * math.cos(yaw) - sag * math.sin(yaw),
            konum[1] + ileri * math.sin(yaw) + sag * math.cos(yaw))

def goruntu_geldi(msg):
    global son
    if konum is None or time.time() - son < 0.2:    # max 5 Hz
        return
    son = time.time()
    kare = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.width, 3)[:, :, ::-1].copy()  # rgb8 -> BGR
    sonuc = model(kare, conf=GUVEN, verbose=False)[0]
    dizi = Detection2DArray(header=msg.header)
    resim_adi = f"det_{time.time():.1f}.jpg"
    for (x1, y1, x2, y2), guven in zip(sonuc.boxes.xyxy.tolist(), sonuc.boxes.conf.tolist()):
        u, v = (x1 + x2) / 2, (y1 + y2) / 2
        kuzey, dogu = yer_konumu(u, v, msg.width, msg.height)
        d = Detection2D(header=msg.header)
        d.bbox.center.position.x, d.bbox.center.position.y = u, v
        d.bbox.size_x, d.bbox.size_y = x2 - x1, y2 - y1
        h = ObjectHypothesisWithPose()
        h.hypothesis.class_id, h.hypothesis.score = "hotspot", guven
        d.results.append(h)
        dizi.detections.append(d)
        yazici.writerow([f"{time.time():.2f}", f"{guven:.2f}", round(konum[0], 2), round(konum[1], 2),
                         round(-konum[2], 2), round(kuzey, 2), round(dogu, 2), resim_adi])
        cv2.rectangle(kare, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 4)
        cv2.putText(kare, f"hotspot {guven:.2f} N{kuzey:.1f} E{dogu:.1f}", (int(x1), max(int(y1) - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
    csv_dosya.flush()
    tespit_pub.publish(dizi)
    resim_pub.publish(Image(header=msg.header, height=msg.height, width=msg.width, encoding="bgr8",
                            step=msg.width * 3, data=kare.tobytes()))
    if dizi.detections:
        cv2.imwrite(f"{KOK}/data/detections/{resim_adi}", kare)
        print(f"{len(dizi.detections)} hotspot  drone N{konum[0]:.1f} E{konum[1]:.1f}")

node.create_subscription(VehicleOdometry, "/fmu/out/vehicle_odometry", odometri,
                         QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT))
node.create_subscription(Image, "/camera/image", goruntu_geldi, 1)
print("Detection node ready, model:", MODEL)
rclpy.spin(node)
