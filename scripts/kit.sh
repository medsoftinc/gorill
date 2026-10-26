#!/bin/bash
# Desk thermal kit mode (no simulation): Arduino (or kit_mock.py) -> ROS 2 -> live panel at http://localhost:8080
# Usage inside the px4 box:  ~/gorill/scripts/kit.sh          (real Arduino on the laptop hotspot)
#                            ~/gorill/scripts/kit.sh mock     (fake Arduino on this laptop, for testing)
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
cd ~/gorill/scripts
trap 'kill $(jobs -p) 2>/dev/null' EXIT
export PANEL_FAULTS=0               # no survey in kit mode: hide the survey fault list
export HOT_C=${HOT_C:-55}            # mark thermal pixels hotter than this (°C); tune on day 1
python3 -u sensor_kopru.py &
python3 -u termal_kopru.py &
[ "$1" = "mock" ] && python3 -u kit_mock.py &
~/venvs/ai/bin/python -u panel.py
