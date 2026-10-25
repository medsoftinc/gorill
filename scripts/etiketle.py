# Auto-label survey frames in YOLO format using sim knowledge:
# an orange blob counts as a hot-spot only if it sits on a (blue) panel; orange things on the ground are decoys.
import glob, os, random
import cv2
import numpy as np
from klasik_tespit import tespit

KOK = os.path.expanduser("~/gorill")
VERI = f"{KOK}/data/dataset"
PANEL_ALT, PANEL_UST = (100, 80, 60), (130, 255, 255)   # HSV range of the blue panels

def panelde_mi(hsv, x, y, w, h, pay=15):
    y0, y1, x0, x1 = max(y - pay, 0), y + h + pay, max(x - pay, 0), x + w + pay
    halka = cv2.inRange(hsv[y0:y1, x0:x1], PANEL_ALT, PANEL_UST)
    halka[y - y0:y - y0 + h, x - x0:x - x0 + w] = 0       # look only at the ring around the blob
    alan = halka.size - w * h
    return alan > 0 and np.count_nonzero(halka) / alan > 0.25

dosyalar = sorted(glob.glob(f"{KOK}/data/frames/*.png"))
random.seed(0)
random.shuffle(dosyalar)
sayilar = {"hotspot": 0, "decoy": 0, "skipped_frames": 0}
for i, dosya in enumerate(dosyalar):
    bolum = "val" if i % 5 == 0 else "train"
    for alt in ("images", "labels"):
        os.makedirs(f"{VERI}/{alt}/{bolum}", exist_ok=True)
    kare = cv2.imread(dosya)
    H, W = kare.shape[:2]
    hsv = cv2.cvtColor(kare, cv2.COLOR_BGR2HSV)
    satirlar, belirsiz = [], False
    for x, y, w, h in tespit(kare)[0]:
        kenarda = x == 0 or y == 0 or x + w >= W or y + h >= H
        if panelde_mi(hsv, x, y, w, h):
            satirlar.append(f"0 {(x + w / 2) / W:.5f} {(y + h / 2) / H:.5f} {w / W:.5f} {h / H:.5f}")
            sayilar["hotspot"] += 1
        elif kenarda:
            belirsiz = True          # cut by the image edge: can't tell panel or ground -> skip frame
        else:
            sayilar["decoy"] += 1
    if belirsiz:
        sayilar["skipped_frames"] += 1
        continue
    ad = os.path.splitext(os.path.basename(dosya))[0]
    cv2.imwrite(f"{VERI}/images/{bolum}/{ad}.jpg", kare)
    open(f"{VERI}/labels/{bolum}/{ad}.txt", "w").write("\n".join(satirlar))

open(f"{VERI}/data.yaml", "w").write(f"path: {VERI}\ntrain: images/train\nval: images/val\nnames:\n  0: hotspot\n")
print(len(dosyalar), "frames,", sayilar)
