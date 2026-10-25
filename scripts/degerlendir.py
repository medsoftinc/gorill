# Compare the classical colour rule and the YOLO model on the validation set (precision / recall / speed)
import glob, os, sys, time
import cv2
from klasik_tespit import tespit

KOK = os.path.expanduser("~/gorill")
MODEL = sys.argv[1] if len(sys.argv) > 1 else f"{KOK}/models/sunhawk/weights/best_openvino_model"
VAL = f"{KOK}/data/dataset/images/val"
PARLAKLIK = float(os.environ.get("BRIGHTNESS", 1.0))  # e.g. 0.6 = cloudy / evening light test

def iou(a, b):  # boxes as (x1, y1, x2, y2)
    ix, iy = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
    kesisim = ix * iy
    return kesisim / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - kesisim + 1e-9)

def etiketler(dosya, W, H):
    kutular = []
    for satir in open(dosya.replace("/images/", "/labels/").replace(".jpg", ".txt")).read().split("\n"):
        if satir:
            _, cx, cy, w, h = map(float, satir.split())
            kutular.append(((cx - w / 2) * W, (cy - h / 2) * H, (cx + w / 2) * W, (cy + h / 2) * H))
    return kutular

def say(gercek, tahmin):  # true positives, false positives, false negatives at IoU >= 0.5
    eslesen, tp = set(), 0
    for t in tahmin:
        adaylar = [(iou(t, g), j) for j, g in enumerate(gercek) if j not in eslesen]
        if adaylar and max(adaylar)[0] >= 0.5:
            eslesen.add(max(adaylar)[1]); tp += 1
    return tp, len(tahmin) - tp, len(gercek) - tp

def rapor(ad, tp, fp, fn, sure, n):
    p, r = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    print(f"{ad:10s} precision {p:.2f}  recall {r:.2f}  (TP {tp}, FP {fp}, FN {fn})  {1000 * sure / n:.0f} ms/frame")

if __name__ == "__main__":
    from ultralytics import YOLO
    model = YOLO(MODEL, task="detect")
    dosyalar = sorted(glob.glob(f"{VAL}/*.jpg"))
    toplam = {"classical": [0, 0, 0, 0.0], "yolo": [0, 0, 0, 0.0]}
    for d in dosyalar:
        kare = cv2.convertScaleAbs(cv2.imread(d), alpha=PARLAKLIK); H, W = kare.shape[:2]
        gercek = etiketler(d, W, H)
        t0 = time.time(); klasik = [(x, y, x + w, y + h) for x, y, w, h in tespit(kare)[0]]; t1 = time.time()
        yolo = [tuple(b) for b in model(kare, conf=0.4, verbose=False)[0].boxes.xyxy.tolist()]; t2 = time.time()
        for ad, tahmin, sure in (("classical", klasik, t1 - t0), ("yolo", yolo, t2 - t1)):
            s = say(gercek, tahmin)
            for i in range(3): toplam[ad][i] += s[i]
            toplam[ad][3] += sure
    print(len(dosyalar), "validation frames, brightness", PARLAKLIK)
    for ad, (tp, fp, fn, sure) in toplam.items():
        rapor(ad, tp, fp, fn, sure, len(dosyalar))
