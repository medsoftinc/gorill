# Mock desk kit: sends exactly what the Arduino sketch sends (sensor JSON on 5005, MLX90640 frames on 5006).
# Scene: a small panel (~45 °C) on a 25 °C table with one shaded cell turning into a hot-spot (~70 °C).
import json, socket, struct, sys, time
import numpy as np

HEDEF = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
y, x = np.mgrid[0:24, 0:32]
t0, kare_no = time.time(), 0
while True:
    t = time.time() - t0
    sahne = np.full((24, 32), 25.0) + np.random.normal(0, 0.3, (24, 32))
    sahne[4:20, 6:26] = 45.0 + np.random.normal(0, 0.3, (16, 20))            # panel
    sicak = 45 + min(t / 10, 1) * 25                                           # hot-spot warms up in 10 s
    sahne[(y - 11) ** 2 + (x - 17) ** 2 <= 4] = sicak
    duz = (sahne.flatten() * 100).astype("<i2")
    for parca in (0, 1):
        soket.sendto(b"TH" + bytes([kare_no % 256, parca]) + duz[parca * 384:(parca + 1) * 384].tobytes(), (HEDEF, 5006))
    kare_no += 1
    if kare_no % 2 == 0:
        mesaj = {"id": "ges-arduino-1", "irr": 850, "t_panel": 45.2, "t_panel2": 44.8, "v": 17.6, "i": 0.52,
                 "p": 9.15, "t_max": round(float(sahne.max()), 1)}
        soket.sendto(json.dumps(mesaj).encode(), (HEDEF, 5005))
    time.sleep(0.5)
