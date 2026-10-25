# Mission gate: start the survey only when irradiance stays >= 600 W/m² for 10 s (thermography needs strong sun)
import os, subprocess, time
import rclpy
import yaml
from std_msgs.msg import Float32

KOK = os.path.expanduser("~/gorill")
s = yaml.safe_load(open(f"{KOK}/config/site.yaml"))["sensor"]
rclpy.init()
node = rclpy.create_node("gorev_kapisi")
yeterli_beri, basladi = None, False

def isinim(msg):
    global yeterli_beri, basladi
    if basladi:
        return
    if msg.data < s["min_irradiance"]:
        yeterli_beri = None
        print(f"{msg.data:.0f} W/m² – waiting for sun")
        return
    yeterli_beri = yeterli_beri or time.time()
    bekleme = time.time() - yeterli_beri
    print(f"{msg.data:.0f} W/m² – OK for {bekleme:.0f}/{s['stable_seconds']} s")
    if bekleme >= s["stable_seconds"]:
        basladi = True
        print("Irradiance stable -> starting survey (tarama.py)")
        if os.environ.get("DRY_RUN"):
            return
        subprocess.Popen(["python3", f"{KOK}/scripts/tarama.py"], cwd=f"{KOK}/scripts")

node.create_subscription(Float32, "/site/irradiance", isinim, 10)
rclpy.spin(node)
