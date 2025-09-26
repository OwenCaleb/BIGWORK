# create_radar_data.py
# 用于创建 ./radar/info 与 ./radar/pred，并写入示例雷达数据（CSV/JSON）
from pathlib import Path
import json
import random
from datetime import datetime, timedelta
import csv

ROOT = Path(".").resolve()
DIR_INFO = ROOT / "radar" / "info"
DIR_PRED = ROOT / "radar" / "pred"

def ensure_dirs():
    DIR_INFO.mkdir(parents=True, exist_ok=True)
    DIR_PRED.mkdir(parents=True, exist_ok=True)

def gen_tracks(n=120, start_time=None, radar_id="RADAR-A", seed=2025):
    """生成 n 条模拟点迹/航迹记录（info 用）"""
    random.seed(seed)
    base_t = start_time or datetime.utcnow().replace(microsecond=0)
    rows = []
    # 模拟 3 条目标，每条 40 帧（合计 ~120）
    for track_id in ["T001", "T002", "T003"]:
        lat0 = 31.20 + random.uniform(-0.1, 0.1)
        lon0 = 121.40 + random.uniform(-0.1, 0.1)
        v_ground = random.uniform(120, 230)    # m/s
        heading = random.uniform(0, 360)       # deg
        for k in range(n // 3):
            t = base_t + timedelta(seconds=2*k)
            lat = lat0 + 0.0002 * k * random.uniform(0.95, 1.05)
            lon = lon0 + 0.00025 * k * random.uniform(0.95, 1.05)
            rng_km = random.uniform(5, 60)
            az_deg = (heading + 0.5*k) % 360
            vel_mps = v_ground + random.uniform(-5, 5)
            snr_db = random.uniform(8, 25)
            q = random.choice([0.7, 0.8, 0.9, 1.0])  # 质量/置信
            rows.append({
                "timestamp_utc": t.isoformat() + "Z",
                "radar_id": radar_id,
                "track_id": track_id,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "range_km": round(rng_km, 3),
                "az_deg": round(az_deg, 2),
                "vel_mps": round(vel_mps, 2),
                "snr_db": round(snr_db, 1),
                "quality": q
            })
    return rows

def gen_preds_from_tracks(tracks):
    """根据 info 生成一个简化的“预测/告警”列表（pred 用）"""
    # 逻辑：速度>200 且 SNR>15 的航迹，给一个“关注”告警，演示字段
    preds = []
    for r in tracks[::5]:  # 每5帧抽一条
        flag = (r["vel_mps"] > 200) and (r["snr_db"] > 15)
        preds.append({
            "timestamp_utc": r["timestamp_utc"],
            "radar_id": r["radar_id"],
            "track_id": r["track_id"],
            "lat": r["lat"],
            "lon": r["lon"],
            "az_deg": r["az_deg"],
            "vel_mps": r["vel_mps"],
            "snr_db": r["snr_db"],
            "alert": "watch" if flag else "normal",
            "score": 0.85 if flag else 0.35
        })
    return preds

def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

def write_json(path, rows):
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    ensure_dirs()
    tracks = gen_tracks(n=120, radar_id="RADAR-A")
    preds = gen_preds_from_tracks(tracks)

    # 写入 CSV（info）
    csv_info = DIR_INFO / "radar_info_sample.csv"
    write_csv(csv_info, tracks, fieldnames=list(tracks[0].keys()))

    # 同时写一份 JSON（方便你选用）
    json_info = DIR_INFO / "radar_info_sample.json"
    write_json(json_info, tracks)

    # 写入 CSV（pred）
    csv_pred = DIR_PRED / "radar_pred_sample.csv"
    write_csv(csv_pred, preds, fieldnames=list(preds[0].keys()))

    json_pred = DIR_PRED / "radar_pred_sample.json"
    write_json(json_pred, preds)

    print(f"[OK] 写入：{csv_info}")
    print(f"[OK] 写入：{json_info}")
    print(f"[OK] 写入：{csv_pred}")
    print(f"[OK] 写入：{json_pred}")
