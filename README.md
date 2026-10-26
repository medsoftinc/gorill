# SunHawk (working name)

**Autonomous drone inspection of solar power plants (GES): fly, find the faulty panel, report it.**

A ground sensor waits for strong sun, an autonomous drone flies a lawnmower route over the panel rows,
an on-board AI model finds hot-spots in the camera image, each fault gets a row/module number and a position,
and a PDF report with a fault map and a yearly loss estimate comes out at the end. Simulation first; real hardware later.

## How it works
```
Arduino (irradiance, panel temp) --WiFi/UDP--> sensor_kopru --ROS 2--> gorev_kapisi (>= 600 W/m² for 10 s)
        --> tarama.py (PX4 offboard, lawnmower route from config/site.yaml, battery RTL at 30 %)
camera --ros_gz_bridge--> /camera/image --> tespit_dugumu.py (YOLO11n, OpenVINO INT8)
        --> /detections, /camera/annotated, detections.csv (drone + ground position)
        --> rapor.py (merge repeated detections -> faults -> fault map -> loss estimate -> PDF)
```

## Tech stack
PX4 v1.17 · Gazebo Harmonic · ROS 2 Jazzy · Micro XRCE-DDS · QGroundControl · Python · YOLO11 (Ultralytics) · OpenVINO · fpdf2 · Arduino Nano RP2040 Connect

## Status
- [x] Module 0: Setup (PX4 SITL, Gazebo, ROS 2, PX4 ↔ ROS 2 bridge)
- [x] Module 1: Controlling the drone from code (takeoff, go to point, search, land)
- [x] Module 2: Camera drone + solar site world, camera image in ROS 2, frame recorder
- [x] Module 3: Site as data, lawnmower route (+ QGC plan), survey flight, position-tagged photos, battery RTL
- [x] Module 4: AI fault detection: classical baseline, auto-labelled sim dataset, YOLO11n training, OpenVINO, ROS 2 detection node
- [~] Module 5: Ground sensor → automatic mission start: software done with a simulated sensor; Arduino sketch drafted, not flashed
- [x] Module 6: Report engine: fault map, loss estimate, automatic PDF; one-command demo `scripts/demo.sh`; live panel; simulated thermal camera
- [ ] Module 7–9: Real hardware (Holybro X500 v2 + Pixhawk 6C, Jetson Orin Nano, thermal camera), field test

Step-by-step log: [`PROGRESS.md`](PROGRESS.md).

## Results (simulation)
| Method | Precision | Recall | Dim light (50 %) | Speed (laptop CPU) |
|---|---|---|---|---|
| Classical colour threshold | 0.63 (false alarms on orange ground decoys) | 0.98 | finds nothing | 2 ms |
| YOLO11n, OpenVINO INT8 | 0.93 | 0.98 | unchanged | 26 ms |

Live survey with the detection node: 7/7 hot-spots found, ~0.3 m position error, no decoys reported.
Details: [`docs/results_module4.md`](docs/results_module4.md), sample report: [`docs/sample_report/`](docs/sample_report/).

## How to run
All commands run inside the Distrobox box `px4` (Ubuntu 24.04); AI code uses the venv `~/venvs/ai`.
1. Simulation (host terminal): `px4ges` → starts Agent, camera bridge and PX4 + Gazebo with the `ges_site` world.
2. Full demo: `~/gorill/scripts/demo.sh` → simulated sensor, gate, survey flight, live detection, PDF in `data/report/`;
   the view-only live panel opens at http://localhost:8080 (RGB + thermal view, map, faults). Flight control stays in QGC.
3. Desk thermal kit (MLX90640 + Arduino): `~/gorill/scripts/kit.sh` (or `kit.sh mock` without hardware), see [`docs/masa_seti.md`](docs/masa_seti.md).
4. Pieces on their own:
   - `python3 scripts/rota.py`: route + QGC plan (`missions/ges_tarama.plan`)
   - `python3 scripts/tarama.py`: fly the survey
   - `~/venvs/ai/bin/python scripts/tespit_dugumu.py`: detection node (view `/camera/annotated` in `rqt_image_view`)
   - `~/venvs/ai/bin/python scripts/rapor.py`: report from `data/detections/detections.csv`
   - Training data and model: `scripts/etiketle.py`, `notebooks/train_colab.ipynb`, `scripts/degerlendir.py`

## Limitations (honest)
- The simulated thermal camera shows temperatures we assign to objects, not real heat physics; the RGB detector is trained on RGB frames. The sim model proves the pipeline; a field model must be trained on real thermal data (see [`docs/datasets.md`](docs/datasets.md)).
- The dataset is small and synthetic, and labels come from sim knowledge.
- The loss estimate is an assumption model (module power × hot-spot loss share × yearly yield × price), not a measurement.
- Ground positions assume level flight; detections seen in fewer than 5 frames are dropped.
- Module 5 hardware is not built yet; the sensor is simulated.

## Repository layout
- `scripts/`: drone control, survey, camera, AI, sensor and report code
- `config/site.yaml`: site description, survey, camera, safety, loss model, sensor settings
- `worlds/ges_site.sdf`: Gazebo solar site with panel rows, hot-spots and decoys
- `arduino/`: ground sensor sketch (draft)
- `docs/`: dataset review, results, sample report
- `ogrenme/`: learning history (Python basics, an earlier ROS 2 ground-robot exercise)

## Project history
Started in October 2026 as GORİLL, a drone detection and tracking prototype (steps 001–017); from step 018 it became SunHawk, solar panel inspection, reusing the same PX4 / ROS 2 / Gazebo base.

## Author
Fırat Serhatlı, Software Engineering, Toros University
