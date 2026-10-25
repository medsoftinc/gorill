#!/bin/bash
pkill -f "[M]icroXRCEAgent"
pkill -f "[p]arameter_bridge"
pkill -9 -f "[g]z sim"
sleep 1
MicroXRCEAgent udp4 -p 8888 > /tmp/xrce_agent.log 2>&1 &
CAM=/world/ges_site/model/x500_mono_cam_down_0/link/camera_link/sensor/imager/image
(source /opt/ros/jazzy/setup.bash && ros2 run ros_gz_bridge parameter_bridge "$CAM@sensor_msgs/msg/Image[gz.msgs.Image" --ros-args -r "$CAM:=/camera/image") > /tmp/cam_bridge.log 2>&1 &
unset GZ_CONFIG_PATH
cd ~/PX4-Autopilot && PX4_GZ_WORLD=ges_site make px4_sitl gz_x500_mono_cam_down
