# Live monitoring panel (view only): RGB + thermal video, site map with drone and faults, status.
# Open http://localhost:8080 in the browser. Flight control stays in QGroundControl.
import json, math, os, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import cv2
import numpy as np
import rclpy
import rclpy.executors
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import String
from px4_msgs.msg import VehicleOdometry, VehicleStatus, BatteryStatus
import rapor
from rota import rota, site

KOK = os.path.expanduser("~/gorill")
SICAK = float(os.environ.get("HOT_C", 60))   # °C: thermal pixels above this are marked as hot
MODLAR = {2: "Position", 3: "Mission", 4: "Hold", 5: "Return (RTL)", 14: "Survey (Offboard)", 17: "Takeoff", 18: "Landing"}

durum = {"north": 0.0, "east": 0.0, "alt": 0.0, "speed": 0.0, "mode": "-", "armed": False, "battery": None,
         "thermal_max": None, "track": [], "faults": [], "sensors": None}
kareler = {"rgb": None, "thermal": None}   # latest JPEG bytes
kilit = threading.Condition()

def jpeg(img):
    return cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 75])[1].tobytes()

son_isaretli = [0.0]

def rgb_geldi(msg, isaretli=True):
    if isaretli:
        son_isaretli[0] = time.time()
    elif time.time() - son_isaretli[0] < 2:   # detection node is running: show its annotated image instead
        return
    img = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.width, 3)
    if msg.encoding == "rgb8":
        img = img[:, :, ::-1]
    with kilit:
        kareler["rgb"] = jpeg(cv2.resize(img, (640, 480)))
        kilit.notify_all()

def termal_geldi(msg):
    sicaklik = np.frombuffer(msg.data, np.uint16).reshape(msg.height, msg.width) / 100.0 - 273.15
    renkli = cv2.applyColorMap(np.clip((sicaklik - 25) / 55 * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    olcek = 640 / msg.width                 # draw boxes after upscaling, so text stays readable for 32x24 too
    renkli = cv2.resize(renkli, (640, int(msg.height * olcek)), interpolation=cv2.INTER_NEAREST)
    maske = (sicaklik > SICAK).astype(np.uint8)
    for k in cv2.findContours(maske, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(k)
        if w * h * olcek * olcek >= 80:
            p1, p2 = (int(x * olcek), int(y * olcek)), (int((x + w) * olcek), int((y + h) * olcek))
            cv2.rectangle(renkli, p1, p2, (255, 255, 255), 2)
            cv2.putText(renkli, f"{sicaklik[y:y + h, x:x + w].max():.0f} C", (p1[0], max(p1[1] - 6, 16)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    durum["thermal_max"] = round(float(sicaklik.max()), 1)
    with kilit:
        kareler["thermal"] = jpeg(renkli)
        kilit.notify_all()

def odometri(msg):
    durum["north"], durum["east"], durum["alt"] = float(msg.position[0]), float(msg.position[1]), -float(msg.position[2])
    durum["speed"] = round(math.hypot(float(msg.velocity[0]), float(msg.velocity[1])), 1)
    iz = durum["track"]
    if not iz or math.dist(iz[-1], (durum["north"], durum["east"])) > 0.5:
        iz.append((round(durum["north"], 1), round(durum["east"], 1)))
        del iz[:-2000]

def arac_durumu(msg):
    durum["mode"] = MODLAR.get(msg.nav_state, f"mode {msg.nav_state}")
    durum["armed"] = msg.arming_state == VehicleStatus.ARMING_STATE_ARMED

def batarya(msg):
    durum["battery"] = round(msg.remaining * 100) if msg.remaining >= 0 else None

def sensorler(msg):
    durum["sensors"] = json.loads(msg.data)

def arizalari_guncelle():
    if os.environ.get("PANEL_FAULTS") == "0":   # desk kit mode: no survey, no fault list
        return
    while True:
        try:
            durum["faults"] = rapor.kayip(rapor.arizalar())
        except (FileNotFoundError, IndexError, ValueError):
            durum["faults"] = []
        time.sleep(2)

class Sunucu(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def gonder(self, tur, veri):
        self.send_response(200)
        self.send_header("Content-Type", tur)
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(veri)

    def do_GET(self):
        if self.path == "/":
            self.gonder("text/html; charset=utf-8", open(f"{KOK}/scripts/panel.html", "rb").read())
        elif self.path == "/state":
            self.gonder("application/json", json.dumps(durum).encode())
        elif self.path == "/site":
            self.gonder("application/json", json.dumps({"rows": site["rows"], "route": rota()}).encode())
        elif self.path in ("/rgb", "/thermal"):
            ad = self.path[1:]
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=kare")
            self.end_headers()
            try:
                while True:
                    with kilit:
                        kilit.wait(1.0)
                        kare = kareler[ad]
                    if kare:
                        self.wfile.write(b"--kare\r\nContent-Type: image/jpeg\r\n\r\n" + kare + b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_error(404)

rclpy.init()
node = rclpy.create_node("panel")
hizli = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
node.create_subscription(Image, "/camera/annotated", rgb_geldi, 1)
node.create_subscription(Image, "/camera/image", lambda m: rgb_geldi(m, isaretli=False), 1)
node.create_subscription(Image, "/thermal/raw", termal_geldi, 1)
node.create_subscription(VehicleOdometry, "/fmu/out/vehicle_odometry", odometri, hizli)
node.create_subscription(VehicleStatus, "/fmu/out/vehicle_status_v1", arac_durumu, hizli)
node.create_subscription(BatteryStatus, "/fmu/out/battery_status_v1", batarya, hizli)
node.create_subscription(String, "/site/sensors", sensorler, 10)
sunucu = ThreadingHTTPServer(("127.0.0.1", 8080), Sunucu)
sunucu.daemon_threads = True
threading.Thread(target=sunucu.serve_forever, daemon=True).start()
threading.Thread(target=arizalari_guncelle, daemon=True).start()
print("Panel: http://localhost:8080")
try:
    rclpy.spin(node)          # Ctrl+C / kill stops ROS and with it the whole panel
except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
    pass
