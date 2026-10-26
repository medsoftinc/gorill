# Hardware-software bridge: Arduino UDP JSON -> ROS 2 topics /site/irradiance and /site/panel_temp
import json, socket
import rclpy
import yaml, os
from std_msgs.msg import Float32, String

site = yaml.safe_load(open(os.path.expanduser("~/gorill/config/site.yaml")))
rclpy.init()
node = rclpy.create_node("sensor_kopru")
isinim_pub = node.create_publisher(Float32, "/site/irradiance", 10)
sicaklik_pub = node.create_publisher(Float32, "/site/panel_temp", 10)
hepsi_pub = node.create_publisher(String, "/site/sensors", 10)   # full JSON (INA219 power etc.)
soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
soket.bind(("0.0.0.0", site["sensor"]["udp_port"]))
soket.settimeout(0.1)

def oku():
    try:
        veri = json.loads(soket.recv(512))
    except (socket.timeout, ValueError):
        return
    isinim_pub.publish(Float32(data=float(veri["irr"])))
    sicaklik_pub.publish(Float32(data=float(veri["t_panel"])))
    hepsi_pub.publish(String(data=json.dumps(veri)))

node.create_timer(0.05, oku)
print("Listening for Arduino on UDP", site["sensor"]["udp_port"])
rclpy.spin(node)
