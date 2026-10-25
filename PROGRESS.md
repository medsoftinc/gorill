# Progress log

| Step | Date | What was done |
|------|------|---------------|
| 001–009 | 2026-10-19 | Environment: Distrobox Ubuntu 24.04 box, PX4 v1.17.0, Gazebo Harmonic, ROS 2 Jazzy, Micro XRCE-DDS Agent v2.4.3, QGroundControl, `px4sim` shortcut |
| Drill 1 | 2026-10-20 | QGroundControl: planned and flew an autonomous mission (takeoff → 3 waypoints → return) |
| Drill 2 | 2026-10-21 | Edited a mission (waypoint altitude 80 m), re-uploaded and flew it |
| 010 | 2026-10-21 | PX4 ↔ ROS 2 bridge: Micro XRCE-DDS Agent running, `/fmu/out/*` topics visible in ROS 2 |
| 011 | 2026-10-21 | Built `px4_msgs` (release/1.17); read live odometry from ROS 2 (z ≈ -2.97 m after takeoff, NED frame) |
| 012 | 2026-10-21 | First Python node: `scripts/ilk_dugum.py` prints the drone's altitude live |
| 013–014 | 2026-10-21 | Offboard + arm from code; drone takes off to 5 m and hovers (`scripts/kalkis.py`) |
| 015 | 2026-10-21 | Fly to a point from code: hover at 5 m, then go 10 m north (`scripts/nokta.py`) |
| 016 | 2026-10-21 | Search motion from code: hover at 5 m and rotate in place (`scripts/arama.py`) |
| 017 | 2026-10-21 | Landing from code: take off, hover, then send land command (`scripts/inis.py`) |
| 018 | 2026-10-25 | Camera drone in simulation: PX4 `x500_mono_cam_down` (downward camera), live image in Gazebo |
| 019 | 2026-10-25 | Solar site world `worlds/ges_site.sdf`: 6 tilted panel rows; flew over them from code and saw panels in the camera |
| 020 | 2026-10-25 | Hot-spot panel added to solar site world |
| 021 | 2026-10-25 | Camera image bridged to ROS 2 (`/camera/image`, ~17 Hz) |
| 022 | 2026-10-25 | Camera recorder node `scripts/kamera_kayit.py`: saves every 10th frame to `data/frames/`; live view with `rqt_image_view` |
| 023 | 2026-10-25 | Site described as data: `config/site.yaml` (boundary, panel rows, survey altitude/speed, camera FOV) |
