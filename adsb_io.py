# adsb_io.py
from pathlib import Path
import pandas as pd, json

def _read_one(p: Path) -> pd.DataFrame:
    if p.suffix.lower()==".csv": return pd.read_csv(p)
    with p.open("r", encoding="utf-8") as f: return pd.DataFrame(json.load(f))

def _normalize_time_num(df: pd.DataFrame, time_col="timestamp_utc"):
    if time_col in df.columns:
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce", utc=True)
    for c in ("lat","lon","alt_baro_ft","gs_mps","trk_deg","roc_mps","score"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def load_adsb_info(root: str | Path = "./adsb/info") -> pd.DataFrame:
    root = Path(root)
    files = sorted([*root.glob("adsb_info_*.*"), *root.glob("*.*")])
    files = [p for p in files if p.suffix.lower() in (".csv",".json")]
    if not files: return pd.DataFrame()
    df = pd.concat([_read_one(p) for p in files], ignore_index=True)
    return _normalize_time_num(df)

def load_adsb_pred(root: str | Path = "./adsb/pred") -> pd.DataFrame:
    root = Path(root)
    files = sorted([*root.glob("adsb_pred_*.*"), *root.glob("*.*")])
    files = [p for p in files if p.suffix.lower() in (".csv",".json")]
    if not files: return pd.DataFrame()
    df = pd.concat([_read_one(p) for p in files], ignore_index=True)
    return _normalize_time_num(df)

if __name__ == "__main__":
    info = load_adsb_info()
    print(f"Loaded ADS-B info: {len(info)} records")
    print(info.head())

    # pred = load_adsb_pred()
    # print(f"Loaded ADS-B pred: {len(pred)} records")
    # print(pred.head())