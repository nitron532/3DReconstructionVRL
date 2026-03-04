#!/usr/bin/env python3
import csv
import math
import os
from pathlib import Path

# ============================================================
# ABSOLUTE PATHS (edit only these if your paths move)
# ============================================================
IMGS_DIR = Path("/home/linghe-zhang/vision-pipeline/vision-pipeline/colmap/imgs")
CSV_PATH = IMGS_DIR / "campbell.csv"
COLMAP_ALIGNED_MODEL = Path("/home/linghe-zhang/vision-pipeline/vision-pipeline/colmap/sparse/0_aligned")
OUT_HTML = IMGS_DIR / "campbell_map.html"

# UCSB ENU ORIGIN (edit to your chosen center point)
UCSB_LAT0_DEG = 34.4140
UCSB_LON0_DEG = -119.8489
UCSB_H0_M = 0.0  # ellipsoidal height for the origin


# ============================================================
# WGS84 helpers: LLH <-> ECEF <-> ENU
# ============================================================
_WGS84_A = 6378137.0
_WGS84_E2 = 6.69437999014e-3

def geodetic_to_ecef(lat_deg: float, lon_deg: float, h_m: float):
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)

    N = _WGS84_A / math.sqrt(1.0 - _WGS84_E2 * sin_lat * sin_lat)
    x = (N + h_m) * cos_lat * cos_lon
    y = (N + h_m) * cos_lat * sin_lon
    z = (N * (1.0 - _WGS84_E2) + h_m) * sin_lat
    return x, y, z

def ecef_to_geodetic(x: float, y: float, z: float):
    # iterative (good enough for plotting)
    lon = math.atan2(y, x)
    p = math.sqrt(x*x + y*y)
    lat = math.atan2(z, p * (1 - _WGS84_E2))
    for _ in range(8):
        sin_lat = math.sin(lat)
        N = _WGS84_A / math.sqrt(1.0 - _WGS84_E2 * sin_lat * sin_lat)
        h = p / math.cos(lat) - N
        lat = math.atan2(z, p * (1 - _WGS84_E2 * (N / (N + h))))
    sin_lat = math.sin(lat)
    N = _WGS84_A / math.sqrt(1.0 - _WGS84_E2 * sin_lat * sin_lat)
    h = p / math.cos(lat) - N
    return math.degrees(lat), math.degrees(lon), h

def ecef_to_enu(x, y, z, lat0_deg, lon0_deg, x0, y0, z0):
    lat0 = math.radians(lat0_deg)
    lon0 = math.radians(lon0_deg)
    dx, dy, dz = x - x0, y - y0, z - z0

    slat, clat = math.sin(lat0), math.cos(lat0)
    slon, clon = math.sin(lon0), math.cos(lon0)

    e = -slon * dx + clon * dy
    n = -clon * slat * dx - slon * slat * dy + clat * dz
    u =  clon * clat * dx + slon * clat * dy + slat * dz
    return e, n, u

def enu_to_ecef(e, n, u, lat0_deg, lon0_deg, x0, y0, z0):
    lat0 = math.radians(lat0_deg)
    lon0 = math.radians(lon0_deg)
    slat, clat = math.sin(lat0), math.cos(lat0)
    slon, clon = math.sin(lon0), math.cos(lon0)

    dx = -slon * e - clon * slat * n + clon * clat * u
    dy =  clon * e - slon * slat * n + slon * clat * u
    dz =              clat * n +         slat * u
    return x0 + dx, y0 + dy, z0 + dz

def llh_to_enu(lat_deg: float, lon_deg: float, h_m: float,
               lat0_deg: float, lon0_deg: float, h0_m: float):
    x0, y0, z0 = geodetic_to_ecef(lat0_deg, lon0_deg, h0_m)
    x, y, z = geodetic_to_ecef(lat_deg, lon_deg, h_m)
    return ecef_to_enu(x, y, z, lat0_deg, lon0_deg, x0, y0, z0)

def enu_to_llh(e: float, n: float, u: float,
               lat0_deg: float, lon0_deg: float, h0_m: float):
    x0, y0, z0 = geodetic_to_ecef(lat0_deg, lon0_deg, h0_m)
    x, y, z = enu_to_ecef(e, n, u, lat0_deg, lon0_deg, x0, y0, z0)
    return ecef_to_geodetic(x, y, z)


# ============================================================
# 1) Parse campbell.csv and assign rows to IMG_*.jpg by order
# ============================================================
def list_imgs_sorted(imgs_dir: Path):
    exts = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
    imgs = [p.name for p in imgs_dir.iterdir() if p.is_file() and p.suffix.lower() in exts]
    return sorted(imgs)

def read_campbell_llh(csv_path: Path):
    rows = []
    with csv_path.open(newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            lat = (row.get("Latitude") or "").strip()
            lon = (row.get("Longitude") or "").strip()
            h   = (row.get("Ellipsoidal height") or "").strip()
            name_idx = (row.get("Name") or "").strip()  # typically 1..N
            if not (lat and lon and h):
                continue
            rows.append({
                "row_name": name_idx,
                "lat": float(lat),
                "lon": float(lon),
                "h": float(h),
            })
    return rows

def campbell_to_enu_points(imgs_dir: Path, csv_path: Path,
                           lat0_deg: float, lon0_deg: float, h0_m: float):
    imgs = list_imgs_sorted(imgs_dir)
    gps_rows = read_campbell_llh(csv_path)

    if len(gps_rows) < len(imgs):
        raise SystemExit(f"campbell.csv has {len(gps_rows)} usable rows but imgs has {len(imgs)} images")
    gps_rows = gps_rows[:len(imgs)]

    pts = []
    for img_name, row in zip(imgs, gps_rows):
        e, n, u = llh_to_enu(row["lat"], row["lon"], row["h"], lat0_deg, lon0_deg, h0_m)
        pts.append({
            "img": img_name,
            "csv_name": row["row_name"],  # "1", "2", ...
            "enu": (e, n, u),
            "llh": (row["lat"], row["lon"], row["h"]),
        })
    return pts


# ============================================================
# 2) Read COLMAP aligned camera centers (already in your ENU frame)
# ============================================================
def qvec_to_R(qw, qx, qy, qz):
    # COLMAP convention (qvec): [qw, qx, qy, qz]
    # returns R s.t. x_cam = R * x_world + t
    ww, xx, yy, zz = qw*qw, qx*qx, qy*qy, qz*qz
    R = [
        [ww + xx - yy - zz, 2*(qx*qy - qw*qz),     2*(qx*qz + qw*qy)],
        [2*(qx*qy + qw*qz), ww - xx + yy - zz,     2*(qy*qz - qw*qx)],
        [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx),     ww - xx - yy + zz],
    ]
    return R

def matT_vec_mul(R, t):
    # R^T * t
    return (
        R[0][0]*t[0] + R[1][0]*t[1] + R[2][0]*t[2],
        R[0][1]*t[0] + R[1][1]*t[1] + R[2][1]*t[2],
        R[0][2]*t[0] + R[1][2]*t[1] + R[2][2]*t[2],
    )

def read_colmap_camera_centers_enu(model_path: Path):
    # Use pycolmap if available; fallback to parsing TXT export
    try:
        import pycolmap  # type: ignore
        rec = pycolmap.Reconstruction(str(model_path))
        pts = []
        for _img_id, img in rec.images.items():
            name = img.name
            # Try method
            C = None
            if hasattr(img, "projection_center"):
                try:
                    c = img.projection_center()
                    C = (float(c[0]), float(c[1]), float(c[2]))
                except Exception:
                    C = None
            if C is None:
                # compute C = -R^T t
                q = img.qvec  # (qw,qx,qy,qz)
                t = img.tvec  # (tx,ty,tz)
                R = qvec_to_R(float(q[0]), float(q[1]), float(q[2]), float(q[3]))
                rt = matT_vec_mul(R, (float(t[0]), float(t[1]), float(t[2])))
                C = (-rt[0], -rt[1], -rt[2])
            pts.append({"img": name, "enu": C})
        return pts
    except Exception:
        # fallback: export to TXT then parse first line per image
        tmp_txt = model_path.parent / "tmp_aligned_txt"
        tmp_txt.mkdir(parents=True, exist_ok=True)
        os.system(
            f'colmap model_converter --input_path "{model_path}" --output_path "{tmp_txt}" --output_type TXT'
        )
        images_txt = tmp_txt / "images.txt"
        pts = []
        with images_txt.open() as f:
            for line in f:
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.strip().split()
                if len(parts) == 10 and parts[0].isdigit():
                    # IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID NAME
                    qw, qx, qy, qz = map(float, parts[1:5])
                    tx, ty, tz = map(float, parts[5:8])
                    name = parts[9]
                    R = qvec_to_R(qw, qx, qy, qz)
                    rt = matT_vec_mul(R, (tx, ty, tz))
                    C = (-rt[0], -rt[1], -rt[2])
                    pts.append({"img": name, "enu": C})
        return pts


# ============================================================
# 3) Build an HTML map (Leaflet) and plot GPS(blue) + COLMAP(red)
# ============================================================
def make_leaflet_html(gps_pts, colmap_pts,
                      lat0_deg: float, lon0_deg: float, h0_m: float,
                      out_html: Path):
    # Convert both datasets ENU->lat/lon for display
    def to_marker(pt, color):
        e, n, u = pt["enu"]
        lat, lon, _h = enu_to_llh(e, n, u, lat0_deg, lon0_deg, h0_m)
        return lat, lon, color

    gps_markers = []
    for pt in gps_pts:
        lat, lon, _ = enu_to_llh(pt["enu"][0], pt["enu"][1], pt["enu"][2], lat0_deg, lon0_deg, h0_m)
        gps_markers.append({
            "lat": lat,
            "lon": lon,
            "color": "#1f6feb",  # modern blue
            "label": f'{pt["img"]}  (CSV Name={pt["csv_name"]})',
        })

    # Index gps by image name so we can show paired info if desired
    gps_by_img = {p["img"]: p for p in gps_pts}

    colmap_markers = []
    for pt in colmap_pts:
        lat, lon, _ = enu_to_llh(pt["enu"][0], pt["enu"][1], pt["enu"][2], lat0_deg, lon0_deg, h0_m)
        csv_name = gps_by_img.get(pt["img"], {}).get("csv_name", "?")
        colmap_markers.append({
            "lat": lat,
            "lon": lon,
            "color": "#e11d48",  # modern red
            "label": f'{pt["img"]}  (CSV Name={csv_name})',
        })

    # Center map on mean of GPS markers
    mean_lat = sum(m["lat"] for m in gps_markers) / max(1, len(gps_markers))
    mean_lon = sum(m["lon"] for m in gps_markers) / max(1, len(gps_markers))

        # build lookup for gps markers by image name
    gps_lookup = {p["img"]: p for p in gps_pts}

    lines_js = []
    for pt in colmap_pts:
        name = pt["img"]
        if name not in gps_lookup:
            continue

        # GPS point
        e1, n1, u1 = gps_lookup[name]["enu"]
        lat1, lon1, _ = enu_to_llh(e1, n1, u1, lat0_deg, lon0_deg, h0_m)

        # COLMAP point
        e2, n2, u2 = pt["enu"]
        lat2, lon2, _ = enu_to_llh(e2, n2, u2, lat0_deg, lon0_deg, h0_m)

        lines_js.append(f"""
        L.polyline(
            [[{lat1}, {lon1}], [{lat2}, {lon2}]],
            {{
                color: "#facc15",
                weight: 2,
                opacity: 0.9
            }}
        ).addTo(map);
        """)

    # Simple Leaflet HTML (no deps beyond CDN)
    markers_js = []
    for m in gps_markers + colmap_markers:
        markers_js.append(
            f"""
            L.circleMarker([{m["lat"]}, {m["lon"]}], {{
              radius: 6,
              color: "{m["color"]}",
              weight: 2,
              fillColor: "{m["color"]}",
              fillOpacity: 0.85
            }}).bindPopup({m["label"]!r}).addTo(map);
            """
        )

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Campbell Cameras: GPS (Blue) vs COLMAP 0_aligned (Red)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    html, body, #map {{ height: 100%; margin: 0; }}
    .legend {{
      position: absolute; bottom: 16px; left: 16px; z-index: 9999;
      background: rgba(20,20,20,0.85); color: #fff; padding: 10px 12px;
      border-radius: 10px; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
      font-size: 13px;
    }}
    .dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:8px; }}
  </style>
</head>
<body>
<div id="map"></div>
<div class="legend">
  <div><span class="dot" style="background:#1f6feb;"></span>GPS from campbell.csv (ENU via UCSB origin)</div>
  <div style="margin-top:6px;"><span class="dot" style="background:#e11d48;"></span>COLMAP sparse/0_aligned camera centers</div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  const map = L.map('map').setView([{mean_lat}, {mean_lon}], 18);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 22,
    attribution: '&copy; OpenStreetMap contributors'
  }}).addTo(map);

  {"".join(markers_js)}
  {"".join(lines_js)}
</script>
</body>
</html>
"""
    out_html.write_text(html, encoding="utf-8")


# ============================================================
# End-to-end pipeline
# ============================================================
def step1_convert_csv_to_enu_points():
    return campbell_to_enu_points(IMGS_DIR, CSV_PATH, UCSB_LAT0_DEG, UCSB_LON0_DEG, UCSB_H0_M)

def step2_read_colmap_aligned_camera_centers():
    return read_colmap_camera_centers_enu(COLMAP_ALIGNED_MODEL)

def step3_write_html_map(gps_pts, colmap_pts):
    make_leaflet_html(gps_pts, colmap_pts, UCSB_LAT0_DEG, UCSB_LON0_DEG, UCSB_H0_M, OUT_HTML)
    print(f"Wrote map: {OUT_HTML}")


if __name__ == "__main__":
    gps_pts = step1_convert_csv_to_enu_points()
    colmap_pts = step2_read_colmap_aligned_camera_centers()
    step3_write_html_map(gps_pts, colmap_pts)