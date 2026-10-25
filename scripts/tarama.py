import math
import os
import rclpy
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleOdometry, BatteryStatus
from rota import rota, site

rclpy.init()
node = rclpy.create_node("tarama")
qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.TRANSIENT_LOCAL)
mod_pub = node.create_publisher(OffboardControlMode, "/fmu/in/offboard_control_mode", qos)
hedef_pub = node.create_publisher(TrajectorySetpoint, "/fmu/in/trajectory_setpoint", qos)
komut_pub = node.create_publisher(VehicleCommand, "/fmu/in/vehicle_command", qos)

YUKSEKLIK, HIZ, TOLERANS = site["survey"]["altitude"], site["survey"]["speed"], 1.0
PIL_SINIRI = float(os.environ.get("RTL_BATTERY", site["safety"]["rtl_battery"]))  # RTL_BATTERY=0 disables the check
noktalar = [[0.0, 0.0, -YUKSEKLIK]] + rota()   # first climb above home, then the lawnmower route
sira = 0
havuc = [0.0, 0.0, -YUKSEKLIK]                  # setpoint that slides toward the waypoint at HIZ m/s
konum = None
sayac = 0
bitti = False

def zaman():
    return node.get_clock().now().nanoseconds // 1000

def komut(kod, p1=0.0, p2=0.0):
    komut_pub.publish(VehicleCommand(command=kod, param1=p1, param2=p2, target_system=1, target_component=1,
                                     source_system=1, source_component=1, from_external=True, timestamp=zaman()))

def odometri(msg):
    global konum
    konum = list(msg.position)

def batarya(msg):
    global bitti
    if not bitti and 0 <= msg.remaining < PIL_SINIRI:
        komut(VehicleCommand.VEHICLE_CMD_NAV_RETURN_TO_LAUNCH)
        print(f"Batarya %{msg.remaining * 100:.0f}: tarama yarida kesildi, eve donuyor (RTL). Tamamlanan nokta: {max(sira - 1, 0)}/{len(noktalar) - 1}")
        bitti = True

def her_100ms():
    global sira, sayac, bitti
    if bitti:
        return
    hedef = noktalar[sira]
    fark = [h - c for h, c in zip(hedef, havuc)]
    mesafe = math.dist(hedef, havuc)
    adim = HIZ * 0.1
    for i in range(3):
        havuc[i] = hedef[i] if mesafe <= adim else havuc[i] + fark[i] / mesafe * adim
    mod_pub.publish(OffboardControlMode(position=True, timestamp=zaman()))
    hedef_pub.publish(TrajectorySetpoint(position=havuc, yaw=0.0, timestamp=zaman()))
    if sayac == 10:
        komut(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)
        komut(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)
        print("Offboard + arm komutu gonderildi")
    sayac += 1
    if konum and havuc == hedef and math.dist(konum, hedef) < TOLERANS:
        print(f"Nokta {sira}/{len(noktalar) - 1} tamam: {hedef}")
        sira += 1
        if sira == len(noktalar):
            komut(VehicleCommand.VEHICLE_CMD_NAV_RETURN_TO_LAUNCH)
            print("Tarama bitti, eve donuyor (RTL)")
            bitti = True

node.create_subscription(VehicleOdometry, "/fmu/out/vehicle_odometry", odometri,
                         QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT))
node.create_subscription(BatteryStatus, "/fmu/out/battery_status_v1", batarya,
                         QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT))
node.create_timer(0.1, her_100ms)
rclpy.spin(node)
