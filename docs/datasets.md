# Thermal PV datasets (step 028)

Our Gazebo camera is RGB, not radiometric thermal. The sim model proves the pipeline
(camera → detector → ROS 2 → position-tagged findings); a field model needs real thermal data.

| Dataset | What | Labels | License | Use for us |
|---|---|---|---|---|
| [Raptor Maps InfraredSolarModules](https://github.com/RaptorMaps/InfraredSolarModules) | 20,000 IR crops of single modules, 24×40 px (zip 15.5 MB) | 12 classes (Hot-Spot 251, Hot-Spot-Multi 247, Cell 1,877, Diode 1,499, No-Anomaly 10,000, …) | MIT | Module classifier (second stage after detection) |
| [Roboflow "Panel Hotspot Detection"](https://universe.roboflow.com/project-solar/panel-hotspot-detection-ya3jq) | Aerial thermal drone images | YOLO boxes | CC BY 4.0 | Closest to our task; needs a Roboflow account |
| [Mendeley PV System Thermal Images](https://data.mendeley.com/datasets/82vzccxb6y) | 277 aerial IR images (DJI Matrice 100 + Zenmuse XT) | none | see page | Label ourselves for a small real test set |

Classical baseline: `scripts/klasik_tespit.py` (HSV colour threshold → mask → contours → boxes).
It finds every sim hot-spot but also fires on any orange object (decoys) and breaks with lighting changes —
which is why we train a detector.
