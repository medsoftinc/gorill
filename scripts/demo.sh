#!/bin/bash
# Full SunHawk demo in one command (run inside the px4 box while px4ges is running):
# simulated Arduino -> irradiance gate -> survey flight -> live YOLO detection -> PDF report
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
cd ~/gorill/scripts
AI=~/venvs/ai/bin/python
export MODEL=${MODEL:-$HOME/gorill/models/sunhawk/weights/best_int8_openvino_model}
rm -rf ~/gorill/data/detections
$AI -u tespit_dugumu.py > /tmp/demo_detect.log 2>&1 &
DET=$!
python3 -u sensor_kopru.py > /tmp/demo_bridge.log 2>&1 &
BRIDGE=$!
python3 -u sensor_sim.py > /dev/null 2>&1 &
SENSOR=$!
sleep 5
python3 -u gorev_kapisi.py          # waits for sun, starts tarama.py, returns after landing
kill $DET $BRIDGE $SENSOR
$AI rapor.py
