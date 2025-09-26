# radar_io.py
# 提供读取 ./radar/info 与 ./radar/pred 的便捷函数（支持 CSV/JSON 自动合并）
from pathlib import Path
import json
import pandas as pd

def _read_one(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as f:
            df = pd.DataFrame(json.load(f))
    else:
        raise ValueError(f"Unsupported file: {path}")
    return df

def load_radar_info(root: str | Path = "./radar/info") -> pd.DataFrame:
    """读取 info 源的所有 CSV/JSON，并做基本类型规整"""
    root = Path(root)
    files = sorted([p for p in root.glob("radar_info_*.*") if p.suffix.lower() in (".csv", ".json")])
    if not files:
        # 也允许直接读任意文件名
        files = sorted([p for p in root.glob("*.*") if p.suffix.lower() in (".csv", ".json")])
    dfs = [_read_one(p) for p in files]
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    # 规整字段类型
    if "timestamp_utc" in df.columns:
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], errors="coerce", utc=True)
    for col in ("lat", "lon", "range_km", "az_deg", "vel_mps", "snr_db", "quality"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def load_radar_pred(root: str | Path = "./radar/pred") -> pd.DataFrame:
    """读取 pred 源的所有 CSV/JSON，并做基本类型规整"""
    root = Path(root)
    files = sorted([p for p in root.glob("radar_pred_*.*") if p.suffix.lower() in (".csv", ".json")])
    if not files:
        files = sorted([p for p in root.glob("*.*") if p.suffix.lower() in (".csv", ".json")])
    dfs = [_read_one(p) for p in files]
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    if "timestamp_utc" in df.columns:
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], errors="coerce", utc=True)
    for col in ("lat", "lon", "az_deg", "vel_mps", "snr_db", "score"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df
 

if __name__ == "__main__":
    # 简单测试
    info = load_radar_info()
    print(f"Loaded radar info: {len(info)} records")
    print(info.head())

    # pred = load_radar_pred()
    # print(f"Loaded radar pred: {len(pred)} records")
    # print(pred.head())
