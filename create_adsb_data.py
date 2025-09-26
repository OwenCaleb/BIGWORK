# create_adsb_data.py
from pathlib import Path
from datetime import datetime, timedelta
import random, json, csv

ROOT = Path(".").resolve()
DIR_INFO = ROOT / "adsb" / "info"
DIR_PRED = ROOT / "adsb" / "pred"

def ensure_dirs():
    DIR_INFO.mkdir(parents=True, exist_ok=True)
    DIR_PRED.mkdir(parents=True, exist_ok=True)

def gen_adsb_msgs(n=150, seed=2025):
    """生成 ADS-B 样例点：icao24、callsign、位置/高度/速度/航向/爬升率 等"""
    random.seed(seed)
    base_t = datetime.utcnow().replace(microsecond=0)
    rows = []
    for icao24, callsign in [("abcd12","MU5123"), ("beef99","CCA178"), ("c0ffee","CSC888")]:
        lat0 = 31.20 + random.uniform(-0.15, 0.15)
        lon0 = 121.40 + random.uniform(-0.15, 0.15)
        alt0 = random.randint(2000, 4000) * 3.28084  # ft
        gs0  = random.uniform(110, 230)              # 对地速度 m/s
        trk0 = random.uniform(0, 360)                # 航向 deg
        for k in range(n // 3):
            t = base_t + timedelta(seconds=2*k)
            rows.append({
                "timestamp_utc": t.isoformat() + "Z",
                "icao24": icao24,
                "callsign": callsign,
                "lat": round(lat0 + 0.00025*k*random.uniform(0.95,1.05), 6),
                "lon": round(lon0 + 0.00020*k*random.uniform(0.95,1.05), 6),
                "alt_baro_ft": round(alt0 + 20*k*random.uniform(-0.2, 0.2), 1),
                "gs_mps": round(gs0 + random.uniform(-5,5), 2),
                "trk_deg": round((trk0 + 0.3*k) % 360, 2),
                "roc_mps": round(random.uniform(-5, 5), 2),   # rate of climb
                "squawk": random.choice(["", "7500", "7600", "7700", ""]),
                "nacp": random.choice([7,8,9,10]),
                "nic": random.choice([6,7,8]),
                "src": "adsb"
            })
    return rows

def simple_alerts(rows):
    """构造一个非常轻量的告警示例：低高度+低速 或 紧急应答码"""
    preds = []
    for r in rows[::5]:
        low_alt = r["alt_baro_ft"] < 3000  # 仅示例
        low_spd = r["gs_mps"] < 120
        emer    = r["squawk"] in {"7500","7600","7700"}
        alert   = "emergency" if emer else ("watch" if (low_alt and low_spd) else "normal")
        score   = 0.95 if emer else (0.75 if (low_alt and low_spd) else 0.35)
        preds.append({
            "timestamp_utc": r["timestamp_utc"],
            "icao24": r["icao24"],
            "callsign": r["callsign"],
            "lat": r["lat"],
            "lon": r["lon"],
            "alt_baro_ft": r["alt_baro_ft"],
            "gs_mps": r["gs_mps"],
            "trk_deg": r["trk_deg"],
            "alert": alert,
            "score": score
        })
    return preds

def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

def write_json(path, rows):
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    ensure_dirs()
    msgs = gen_adsb_msgs()
    preds = simple_alerts(msgs)

    p1 = DIR_INFO / "adsb_info_sample.csv";   write_csv(p1, msgs)
    p2 = DIR_INFO / "adsb_info_sample.json";  write_json(p2, msgs)
    p3 = DIR_PRED / "adsb_pred_sample.csv";   write_csv(p3, preds)
    p4 = DIR_PRED / "adsb_pred_sample.json";  write_json(p4, preds)
    print("[OK] ADS-B 数据已生成：", p1, p2, p3, p4, sep="\n- ")
