# SIMULATED ground-station Arduino: sends the same UDP JSON the real board will send over WiFi.
# Irradiance rises like a morning sun: 300 -> 900 W/m² over ~60 s.
import json, socket, sys, time

HEDEF = (sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1", 5005)
soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
t0 = time.time()
while True:
    t = time.time() - t0
    isinim = min(300 + 10 * t, 900)
    mesaj = {"id": "ges-arduino-1", "irr": round(isinim), "t_panel": round(25 + isinim / 30, 1), "t_amb": 24.0}
    soket.sendto(json.dumps(mesaj).encode(), HEDEF)
    print(mesaj)
    time.sleep(1)
