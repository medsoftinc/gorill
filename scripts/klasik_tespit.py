# Classical hot-spot detector: colour threshold -> mask -> contours -> boxes (no AI)
import glob, os, sys
import cv2

KOK = os.path.expanduser("~/gorill")
klasor = sys.argv[1] if len(sys.argv) > 1 else f"{KOK}/data/frames"
cikti = f"{KOK}/data/klasik"
os.makedirs(cikti, exist_ok=True)

ALT, UST = (15, 150, 150), (35, 255, 255)   # HSV range of the orange/yellow hot-spot (OpenCV hue 0-179)
MIN_ALAN = 100                              # ignore blobs smaller than this many pixels

def tespit(kare):
    hsv = cv2.cvtColor(kare, cv2.COLOR_BGR2HSV)
    maske = cv2.inRange(hsv, ALT, UST)
    konturlar, _ = cv2.findContours(maske, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [cv2.boundingRect(k) for k in konturlar if cv2.contourArea(k) >= MIN_ALAN], maske

if __name__ == "__main__":
    for dosya in sorted(glob.glob(f"{klasor}/*.png")):
        kare = cv2.imread(dosya)
        kutular, maske = tespit(kare)
        for x, y, w, h in kutular:
            cv2.rectangle(kare, (x, y), (x + w, y + h), (0, 0, 255), 4)
        if kutular:
            cv2.imwrite(f"{cikti}/{os.path.basename(dosya)}", kare)
            cv2.imwrite(f"{cikti}/maske_{os.path.basename(dosya)}", maske)
        print(os.path.basename(dosya), "hot-spot:", len(kutular), kutular)
