# Module 4 results – classical rule vs YOLO (validation set, 109 frames, 132 hot-spots)

| Method | Light | Precision | Recall | Speed (laptop CPU) |
|---|---|---|---|---|
| Classical colour threshold | normal | 0.63 (77 false alarms on ground decoys) | 0.98 | 2 ms |
| YOLO11n (OpenVINO FP32) | normal | 0.93 | 0.98 | 31 ms |
| Classical | 60 % | 0.66 | 0.95 | 2 ms |
| YOLO11n | 60 % | 0.93 | 0.98 | 32 ms |
| Classical | 50 % | – | **0.00** (rule breaks) | 2 ms |
| YOLO11n | 50 % | 0.94 | 0.98 | 31 ms |
| YOLO11n (OpenVINO INT8) | normal | 0.93 | 0.98 | 26 ms (~38 FPS) |

- Precision = of the boxes we drew, how many were real faults. Recall = of the real faults, how many we found.
- Labels were produced with sim knowledge (orange on a panel), so the classical rule's recall is high by construction;
  the interesting numbers are its false alarms on decoys and its collapse in dim light.
- Run: `~/venvs/ai/bin/python scripts/degerlendir.py [model]`, `BRIGHTNESS=0.5` for the dim-light test.
