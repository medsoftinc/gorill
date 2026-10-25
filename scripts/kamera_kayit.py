import csv, math, os, time
import numpy as np
import rclpy
import yaml
from rclpy.qos import QoSProfile, ReliabilityPolicy
from PIL import Image as PilImage
from sensor_msgs.msg import Image
from px4_msgs.msg import VehicleOdometry

KOK = os.path.expanduser("~/gorill")
KLASOR = f"{KOK}/data/frames"
os.makedirs(KLASOR, exist_ok=True)
site = yaml.safe_load(open(f"{KOK}/config/site.yaml"))

# Ground width seen by the camera (along the flight direction) and the frame spacing for the wanted overlap
s = site["survey"]
iz_genisligi = 2 * s["altitude"] * math.tan(site["camera"]["hfov_rad"] / 2)
ARALIK = float(os.environ.get("FRAME_EVERY", (1 - s["forward_overlap"]) * iz_genisligi / s["speed"]))
print(f"Footprint {iz_genisligi:.1f} m -> one frame every {ARALIK:.1f} s")

rclpy.init()
node = rclpy.create_node("kamera_kayit")
konum = None
son_kayit = 0.0
csv_dosya = open(f"{KLASOR}/frames.csv", "a", newline="")
yazici = csv.writer(csv_dosya)

def odometri(msg):
    global konum
    konum = msg.position

def goruntu_geldi(msg):
    global son_kayit
    if konum is None or time.time() - son_kayit < ARALIK:
        return
    son_kayit = time.time()
    kanal = 4 if msg.encoding in ("rgba8", "bgra8") else 3
    kare = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.step)[:, :msg.width * kanal]
    kare = kare.reshape(msg.height, msg.width, kanal)[:, :, :3]
    if msg.encoding.startswith("bgr"):
        kare = kare[:, :, ::-1]
    n, e, d = (round(float(v), 2) for v in konum)
    dosya = f"kare_{int(son_kayit)}_N{n}_E{e}.png"
    PilImage.fromarray(kare).save(os.path.join(KLASOR, dosya))
    yazici.writerow([dosya, n, e, -d])
    csv_dosya.flush()
    print("Kaydedildi:", dosya)

node.create_subscription(VehicleOdometry, "/fmu/out/vehicle_odometry", odometri,
                         QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT))
node.create_subscription(Image, "/camera/image", goruntu_geldi, 10)
rclpy.spin(node)
