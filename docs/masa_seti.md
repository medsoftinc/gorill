# Masa başı termal set: parça listesi, bağlantı, ilk gün testleri

Amaç: Drone olmadan, gerçek bir güneş panelinde gerçek bir hot-spot oluşturmak, onu gerçek termal kamerayla görmek
ve sistemin geri kalanını (ROS 2, canlı panel, rapor) aynen kullanmak.

## 1. Kesin parça listesi

| # | Parça | Doğru model / dikkat | Adet (+yedek) |
|---|---|---|---|
| 1 | Termal kamera | **MLX90640ESF-BAB** (55°×35°) breakout, 3,3 V, I2C. **BAA alma**: o 110° geniş açılı, panel başına daha az piksel düşer. Örnek: Waveshare "MLX90640-D55". | 1 |
| 2 | Akım/gerilim sensörü | **INA219** breakout, üzerinde **0,1 Ω (R100)** şönt, I2C adresi 0x40. Bus gerilimi en fazla 26 V. | 1 (+1) |
| 3 | Sıcaklık sensörü | **DS18B20 su geçirmez prob**, 1 m kablolu (kırmızı/siyah/sarı uçlu) | 2 (+1) |
| 4 | Direnç | 4,7 kΩ, 1/4 W (DS18B20 için) | 1 (+paket) |
| 5 | Güneş paneli | **10 W, 12 V, monokristal**. Voc ≈ 21–22 V (INA219 limiti 26 V, uygun), Isc ≈ 0,6 A | 1 |
| 6 | Yük direnci | **10 Ω, en az 10 W** (tercihen 25 W alüminyum gövdeli). Panel kısa devreye yakın çalışır, gölgedeki hücre en çok bu durumda ısınır. Direnç ~4 W harcar ve ısınır. | 1 |
| 7 | Referans güneş hücresi | Mini güneş hücresi 0,5–1 W (ör. 5 V 100 mA) + **1 Ω** 1/4 W direnç. Güneş gücünü (W/m²) ölçer. | 1 |
| 8 | Bağlantı | Breadboard, erkek-erkek ve erkek-dişi jumper, panel devresi için 0,5 mm² kablo, 2'li klemens | 1 set |
| — | Elinde var | Arduino Nano RP2040 Connect, USB kablo, powerbank, laptop | — |

BH1750 ışık sensörü **almıyoruz**: en fazla ~65.000 lux ölçebiliyor, tam güneş ~100.000 lux, yani tam güneşte doyar.

## 2. Bağlantı şeması

```
                 3V3 ──┬──────────┬──────────────┬─────────── 4,7k ──┐
                       │          │              │                   │
                 [MLX90640]   [INA219]      [DS18B20 x2]             │
                   SDA SCL     SDA SCL        sarı uç ───────────────┴── D2
 Arduino  A4 ──────┴───┼───────┘   │
          A5 ──────────┴───────────┘
          A0 ──┬── referans hücre (+)        referans hücre (−) ── GND
               └── 1 Ω ── GND
          GND ── tüm sensörlerin GND'si ── panel (−)

 Panel (+) ── INA219 VIN+     INA219 VIN− ── 10 Ω yük direnci ── panel (−)
 Arduino ── USB ── powerbank
```

- MLX90640 ve INA219 aynı I2C hattında: adresler farklı (0x33 ve 0x40), çakışma yok. Arduino'nun kendi çipleri 0x60 ve 0x6A'da, onlar da çakışmaz.
- Panelin (−) ucu Arduino GND'sine bağlanmalı, yoksa INA219 gerilimi yanlış ölçer.
- Panel gerilimi Arduino'ya **asla doğrudan** bağlanmaz; sadece INA219 üzerinden.

## 3. Derleme ve yükleme

Kod laptopta derleniyor (2026-10-26: hatasız; program 125.593 bayt, RAM %20).
Kütüphaneler: WiFiNINA 2.1.1, Adafruit MLX90640 1.1.2, Adafruit INA219 1.2.3, OneWire 2.3.8, DallasTemperature 4.0.6.

```bash
cd ~/gorill/arduino/ges_kit && cp -n arduino_secrets.h.example arduino_secrets.h
~/.local/bin/arduino-cli compile --fqbn arduino:mbed_nano:nanorp2040connect .
~/.local/bin/arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:mbed_nano:nanorp2040connect .
~/.local/bin/arduino-cli monitor -p /dev/ttyACM0 -c baudrate=115200
```
Yüklemeden önce `arduino_secrets.h` içine WiFi adını, şifresini ve laptop IP'sini yaz.

## 4. İlk gün testleri (her biri tek başına, sonra hepsi birlikte)

Arduino'yu USB ile laptopa bağla, `arduino/ges_kit` kodunu yükle, Serial Monitor'ü 115200 baud ile aç.

| Test | Ne yaparsın | Beklenen |
|---|---|---|
| 0. Kart | Kodu yükle | "WiFi connecting…" yazısı gelir |
| 1. I2C taraması | Açılışta otomatik | `I2C devices: 0x33 0x40 0x60 0x6A` |
| 2. Termal kamera | Kameranın önünde elini salla | `MLX90640: OK`, `t_max` ≈ 32–35 °C (el sıcaklığı) |
| 3. Sıcaklık probları | Probları elinde tut | `DS18B20: 2 found`, oda ≈ 20–25 °C, elde ≈ 30 °C'ye çıkar |
| 4. Akım sensörü | Panel güneşte, yük bağlı | `v` ≈ 5–7 V, `i` ≈ 0,4–0,6 A; paneli kapatınca `i` ≈ 0 |
| 5. Işınım | Referans hücreyi gölgele / güneşe çevir | Gölgede `irr` ≈ 0, güneşte yüzlerce W/m². Bilinen bir değere göre `CELL_W_PER_V` ayarlanır |
| 6. WiFi | Laptopta erişim noktasını aç, Arduino bağlansın | Serial'de "WiFi OK, my IP: …" |
| 7. ROS 2 | Laptopta `~/gorill/scripts/kit.sh` | `ros2 topic hz /thermal/raw` ≈ 2 Hz |
| 8. Hepsi birlikte | Tarayıcıda `http://localhost:8080`, bir hücreyi kartonla gölgele | Termal görüntüde 1–5 dakikada sıcak nokta belirir (+10–30 °C), kutu içine alınır |

Donanım gelmeden yazılımı denemek için: `~/gorill/scripts/kit.sh mock` (sahte Arduino, aynı veriyi yollar).

## 5. Güvenlik ve ölçüm notları

- Gölgelenen hücre **80 °C'nin üstüne** çıkabilir: dokunma, uzun süre gölgede bırakma (en fazla birkaç dakika).
- 10 Ω yük direnci ısınır: yanıcı yüzeye koyma.
- Panel gerilimi düşük (en fazla ~22 V DC) ama uçları birbirine değdirme.
- Test **dışarıda, öğlen saatlerinde**, açık havada yapılır (ışınım ≥ 600 W/m²; IEC TS 62446-3).
- İç mekânda **halojen veya akkor lamba kullanma**: kızılötesi yayar, termal kamerayı yanıltır.
- Termal kamerayı panele dik, 1–2 m mesafeden tut; açı arttıkça cam yansıması ölçümü bozar.
- MLX90640 32×24 piksel: tek paneli görmek için yeterli, sahada drone için 640×512 kamera gerekir (şirket aşaması).
