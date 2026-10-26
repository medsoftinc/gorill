#!/bin/bash
pkill -f "[M]icroXRCEAgent"
pkill -f "[p]arameter_bridge"
pkill -9 -f "[g]z sim"
sleep 1
MicroXRCEAgent udp4 -p 8888 > /tmp/xrce_agent.log 2>&1 &
M=/world/ges_site/model/x500_dual_cam_down_0/link
CAM=$M/camera_link/sensor/imager/image
TERMAL=$M/thermal_link/sensor/thermal/image
(source /opt/ros/jazzy/setup.bash && ros2 run ros_gz_bridge parameter_bridge \
  "$CAM@sensor_msgs/msg/Image[gz.msgs.Image" "$TERMAL@sensor_msgs/msg/Image[gz.msgs.Image" \
  --ros-args -r "$CAM:=/camera/image" -r "$TERMAL:=/thermal/raw") > /tmp/cam_bridge.log 2>&1 &
unset GZ_CONFIG_PATH
. ~/PX4-Autopilot/build/px4_sitl_default/rootfs/gz_env.sh   # model/world paths (make used to set these)
# Drone with RGB + thermal camera (gz_models/x500_dual_cam_down), x500 airframe 4014, solar site world
cd ~/PX4-Autopilot/build/px4_sitl_default && PX4_SYS_AUTOSTART=4014 PX4_SIM_MODEL=gz_x500_dual_cam_down PX4_GZ_WORLD=ges_site ./bin/px4 rootfs
