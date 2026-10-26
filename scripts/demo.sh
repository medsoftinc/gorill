#!/bin/bash
# Full SunHawk demo in one command (run inside the px4 box while px4ges is running):
# simulated Arduino -> irradiance gate -> survey flight -> live YOLO detection -> PDF report
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
cd ~/gorill/scripts
AI=~/venvs/ai/bin/python
export MODEL=${MODEL:-$HOME/gorill/models/sunhawk/weights/best_int8_openvino_model}
trap 'kill $(jobs -p) 2>/dev/null' EXIT          # never leave helper nodes running

# 1. Wait until the simulation is up and PX4 is ready to arm (max 2 min)
echo "Waiting for simulation and PX4 preflight checks..."
for i in $(seq 60); do
  if timeout 3 ros2 topic echo --once /fmu/out/vehicle_status_v1 --field pre_flight_checks_pass 2>/dev/null | grep -qi true \
     && timeout 3 ros2 topic echo --once /camera/image --field width 2>/dev/null | grep -q 1280; then
    READY=1; break
  fi
  sleep 2
done
[ -z "$READY" ] && { echo "ERROR: simulation not ready - is px4ges running?"; exit 1; }
echo "Simulation ready"

# 2. Live panel (view only) in the browser, unless it is already running
if ! curl -s -o /dev/null http://localhost:8080/state; then
  setsid $AI -u panel.py > /tmp/demo_panel.log 2>&1 < /dev/null & disown   # keeps running after the demo
  sleep 3
fi
distrobox-host-exec xdg-open http://localhost:8080 > /dev/null 2>&1 || echo "Open http://localhost:8080 in the browser"

# 3. Helper nodes: detection, sensor bridge, simulated Arduino
rm -rf ~/gorill/data/detections
$AI -u tespit_dugumu.py > /tmp/demo_detect.log 2>&1 &
python3 -u sensor_kopru.py > /tmp/demo_bridge.log 2>&1 &
python3 -u sensor_sim.py > /dev/null 2>&1 &
for i in $(seq 30); do grep -q "ready" /tmp/demo_detect.log && break; sleep 1; done

# 4. Gate waits for sun, starts tarama.py and returns after landing (max 10 min)
timeout 600 python3 -u gorev_kapisi.py | grep --line-buffered -vE "W/m"
kill $(jobs -p) 2>/dev/null
sleep 1

# 5. Report
$AI rapor.py | tail -2
