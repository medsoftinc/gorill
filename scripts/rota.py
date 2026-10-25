import json, math, os, yaml

KOK = os.path.expanduser("~/gorill")
site = yaml.safe_load(open(f"{KOK}/config/site.yaml"))
if os.environ.get("SURVEY_ALT"):  # optional override, e.g. SURVEY_ALT=10 for extra training data
    site["survey"]["altitude"] = float(os.environ["SURVEY_ALT"])
EV_LAT, EV_LON = 47.397971057728974, 8.546163739800146  # ges_site.sdf spherical_coordinates

def rota():
    r, s = site["rows"], site["survey"]
    bati, dogu = r["east_start"] - s["end_margin"], r["east_end"] + s["end_margin"]
    noktalar = []
    for i, kuzey in enumerate(r["north"]):
        bas, son = (bati, dogu) if i % 2 == 0 else (dogu, bati)   # every other row flies back
        noktalar += [[kuzey, bas, -s["altitude"]], [kuzey, son, -s["altitude"]]]
    return noktalar

def latlon(kuzey, dogu):
    return (EV_LAT + math.degrees(kuzey / 6378137.0),
            EV_LON + math.degrees(dogu / (6378137.0 * math.cos(math.radians(EV_LAT)))))

def qgc_plan(noktalar, dosya):
    alt = site["survey"]["altitude"]
    items = [{"type": "SimpleItem", "autoContinue": True, "command": 22, "doJumpId": 1, "frame": 3,
              "params": [0, 0, 0, None, EV_LAT, EV_LON, alt]}]
    for i, (n, e, _) in enumerate(noktalar):
        items.append({"type": "SimpleItem", "autoContinue": True, "command": 16, "doJumpId": i + 2,
                      "frame": 3, "params": [0, 0, 0, None, *latlon(n, e), alt]})
    items.append({"type": "SimpleItem", "autoContinue": True, "command": 20, "doJumpId": len(items) + 1,
                  "frame": 2, "params": [0, 0, 0, 0, 0, 0, 0]})
    plan = {"fileType": "Plan", "version": 1, "groundStation": "QGroundControl",
            "geoFence": {"circles": [], "polygons": [], "version": 2},
            "rallyPoints": {"points": [], "version": 2},
            "mission": {"version": 2, "firmwareType": 12, "vehicleType": 2, "cruiseSpeed": 15,
                        "hoverSpeed": site["survey"]["speed"], "plannedHomePosition": [EV_LAT, EV_LON, 0],
                        "items": items}}
    json.dump(plan, open(dosya, "w"), indent=2)

if __name__ == "__main__":
    noktalar = rota()
    for n in noktalar:
        print(n)
    os.makedirs(f"{KOK}/missions", exist_ok=True)
    qgc_plan(noktalar, f"{KOK}/missions/ges_tarama.plan")
    print("QGC plan:", f"{KOK}/missions/ges_tarama.plan")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    r = site["rows"]
    for k in r["north"]:
        plt.plot([r["east_start"], r["east_end"]], [k, k], color="tab:blue", linewidth=8, alpha=0.4)
    plt.plot([0] + [n[1] for n in noktalar], [0] + [n[0] for n in noktalar], "o-", color="tab:orange")
    plt.xlabel("east (m)"); plt.ylabel("north (m)"); plt.title("Survey route"); plt.axis("equal")
    plt.savefig(f"{KOK}/missions/ges_tarama.png", dpi=80)
    print("Route image:", f"{KOK}/missions/ges_tarama.png")
