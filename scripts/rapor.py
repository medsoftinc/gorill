# Inspection report engine: detections.csv -> faults (row/module) -> fault map -> loss estimate -> PDF
import csv, datetime, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml

KOK = os.path.expanduser("~/gorill")
site = yaml.safe_load(open(f"{KOK}/config/site.yaml"))
CIKTI = f"{KOK}/data/report"
os.makedirs(CIKTI, exist_ok=True)
BIRLESTIR = 2.0   # detections closer than this (m) are the same fault
MIN_GORUNTU = 5   # a real fault is seen in many overlapping frames; fewer views = noise (e.g. while turning)

def arizalar(dosya=f"{KOK}/data/detections/detections.csv"):
    """Group repeated detections of the same spot into one fault (overlapping photos see it many times)."""
    gruplar = []
    for satir in csv.reader(open(dosya)):
        guven, kuzey, dogu, resim = float(satir[1]), float(satir[5]), float(satir[6]), satir[7]
        drone = (float(satir[2]), float(satir[3]))
        for g in gruplar:
            if abs(g["n"] - kuzey) < BIRLESTIR and abs(g["e"] - dogu) < BIRLESTIR:
                g["noktalar"].append((kuzey, dogu, guven))
                g["guven"] = max(g["guven"], guven)
                g["resimler"].append((drone, resim))
                g["n"] = sum(p[0] for p in g["noktalar"]) / len(g["noktalar"])
                g["e"] = sum(p[1] for p in g["noktalar"]) / len(g["noktalar"])
                break
        else:
            gruplar.append({"n": kuzey, "e": dogu, "noktalar": [(kuzey, dogu, guven)], "guven": guven, "resimler": [(drone, resim)]})
    r = site["rows"]
    modul_boyu = (r["east_end"] - r["east_start"]) / site["modules"]["per_row"]
    sonuc = []
    for g in gruplar:
        if len(g["noktalar"]) < MIN_GORUNTU:
            continue
        sira = min(range(len(r["north"])), key=lambda i: abs(r["north"][i] - g["n"]))
        modul = int((g["e"] - r["east_start"]) // modul_boyu) + 1
        if abs(r["north"][sira] - g["n"]) > 2.0 or not 1 <= modul <= site["modules"]["per_row"]:
            continue                    # not on a panel row
        # report photo: the frame taken with the drone right above the fault (fault in the image centre)
        _, resim = min(g["resimler"], key=lambda dr: (dr[0][0] - g["n"]) ** 2 + (dr[0][1] - g["e"]) ** 2)
        sonuc.append({"north": round(g["n"], 1), "east": round(g["e"], 1), "row": sira + 1, "module": modul,
                      "views": len(g["noktalar"]), "conf": round(g["guven"], 2), "image": resim})
    sonuc.sort(key=lambda a: (a["row"], a["module"]))
    for i, a in enumerate(sonuc, 1):
        a["id"] = f"F{i}"
    return sonuc

def harita(liste, dosya=f"{CIKTI}/fault_map.png"):
    r = site["rows"]
    fig, ax = plt.subplots(figsize=(8, 7))
    for i, k in enumerate(r["north"]):
        ax.add_patch(plt.Rectangle((r["east_start"], k - 1.0), r["east_end"] - r["east_start"], 2.0, color="tab:blue", alpha=0.35))
        ax.text(r["east_start"] - 1.0, k, f"Row {i + 1}", ha="right", va="center")
    for a in liste:
        ax.plot(a["east"], a["north"], "o", color="red", markersize=10)
        ax.annotate(f'{a["id"]} (M{a["module"]})', (a["east"], a["north"]), xytext=(6, 6), textcoords="offset points", color="darkred")
    ax.plot(0, 0, "k^", markersize=10); ax.annotate("Home", (0, 0), xytext=(6, -12), textcoords="offset points")
    ax.set_xlabel("East (m)"); ax.set_ylabel("North (m)"); ax.set_title(f'{site["name"]} – detected hot-spots')
    ax.set_xlim(r["east_start"] - 6, r["east_end"] + 3); ax.set_aspect("equal"); ax.grid(alpha=0.3)
    fig.savefig(dosya, dpi=110, bbox_inches="tight"); plt.close(fig)
    return dosya

def kayip(liste):
    """Yearly energy/money loss per fault – a simple, clearly stated assumption model."""
    m = site["loss_model"]
    kwh = m["module_power_w"] / 1000 * m["specific_yield_kwh_per_kwp"] * m["hotspot_loss"]
    for a in liste:
        a["loss_kwh"], a["loss_tl"] = round(kwh), round(kwh * m["price_tl_per_kwh"])
    return liste

def pdf(liste, harita_png, dosya=f"{CIKTI}/inspection_report.pdf"):
    from fpdf import FPDF
    m = site["loss_model"]
    doc = FPDF()
    doc.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    doc.add_font("DejaVu", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    doc.add_page()
    doc.set_font("DejaVu", "B", 18); doc.cell(0, 12, "SunHawk – GES Termal Denetim Raporu", new_x="LMARGIN", new_y="NEXT")
    doc.set_font("DejaVu", "", 10)
    doc.cell(0, 6, f'Saha: {site["name"]}   Tarih: {datetime.date.today():%d.%m.%Y}   Uçuş yüksekliği: {site["survey"]["altitude"]:.0f} m',
             new_x="LMARGIN", new_y="NEXT")
    toplam_kwh, toplam_tl = sum(a["loss_kwh"] for a in liste), sum(a["loss_tl"] for a in liste)
    doc.set_font("DejaVu", "B", 12)
    doc.cell(0, 9, f"Bulunan arıza: {len(liste)}   Tahmini yıllık kayıp: {toplam_kwh} kWh ≈ {toplam_tl:,} TL".replace(",", "."),
             new_x="LMARGIN", new_y="NEXT")
    doc.image(harita_png, w=105, x=52)
    doc.ln(2); doc.set_font("DejaVu", "B", 9)
    basliklar = ["ID", "Sıra", "Modül", "Kuzey (m)", "Doğu (m)", "Görüntü", "Güven", "kWh/yıl", "TL/yıl"]
    genislik = [12, 14, 16, 22, 22, 20, 18, 22, 22]
    for b, g in zip(basliklar, genislik):
        doc.cell(g, 7, b, border=1, align="C")
    doc.ln(); doc.set_font("DejaVu", "", 9)
    for a in liste:
        for v, g in zip([a["id"], a["row"], a["module"], a["north"], a["east"], a["views"], a["conf"], a["loss_kwh"], a["loss_tl"]], genislik):
            doc.cell(g, 6, str(v), border=1, align="C")
        doc.ln()
    doc.add_page(); doc.set_font("DejaVu", "B", 12); doc.cell(0, 8, "Arıza görüntüleri", new_x="LMARGIN", new_y="NEXT")
    doc.set_font("DejaVu", "", 9)
    y = doc.get_y()
    for i, a in enumerate(liste):
        if i % 2 == 0 and i > 0:
            y += 72
        if y + 70 > 285:
            doc.add_page(); y = 15
        x = 10 + (i % 2) * 95
        yol = f'{KOK}/data/detections/{a["image"]}'
        if os.path.exists(yol):
            doc.image(yol, x=x, y=y, w=85)
        doc.set_xy(x, y + 64); doc.cell(85, 5, f'{a["id"]}: Sıra {a["row"]}, Modül {a["module"]} (güven {a["conf"]})')
    doc.add_page(); doc.set_font("DejaVu", "B", 12); doc.cell(0, 8, "Varsayımlar ve sınırlar", new_x="LMARGIN", new_y="NEXT")
    doc.set_font("DejaVu", "", 10)
    for satir in [
        f'Kayıp modeli bir tahmindir, ölçüm değildir: modül gücü {m["module_power_w"]} W, bir hot-spot modül üretiminin '
        f'%{m["hotspot_loss"] * 100:.0f}\'ini düşürür, yıllık verim {m["specific_yield_kwh_per_kwp"]} kWh/kWp, elektrik fiyatı {m["price_tl_per_kwh"]} TL/kWh.',
        "Bu rapor simülasyon verisiyle üretildi: kamera RGB, radyometrik termal değil; sıcaklık farkı (ΔT) ölçülmedi.",
        "Tespit modeli küçük bir simülasyon veri setiyle eğitildi; gerçek sahada gerçek termal veriyle yeniden eğitilmelidir.",
        "Termografi için ışınım ≥ 600 W/m² olmalıdır (IEC TS 62446-3).",
        "Konum, drone konumu + kamera açısından hesaplanır; hata payı yaklaşık ±1 m.",
    ]:
        doc.multi_cell(0, 6, "• " + satir); doc.ln(1)
    doc.output(dosya)
    return dosya

if __name__ == "__main__":
    liste = kayip(arizalar())
    for a in liste:
        print(a)
    png = harita(liste)
    print("Map:", png)
    print("PDF:", pdf(liste, png))
    if liste:
        w = csv.DictWriter(open(f"{CIKTI}/faults.csv", "w", newline=""), fieldnames=list(liste[0]))
        w.writeheader(); w.writerows(liste)
