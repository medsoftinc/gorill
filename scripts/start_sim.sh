#!/bin/bash
pkill -f "[M]icroXRCEAgent"
pkill -9 -f "[g]z sim"
sleep 1
MicroXRCEAgent udp4 -p 8888 > /tmp/xrce_agent.log 2>&1 &
unset GZ_CONFIG_PATH
cd ~/PX4-Autopilot && PX4_GZ_WORLD=ges_site make px4_sitl gz_x500_mono_cam_down
