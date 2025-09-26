# create_ground_from_gpt.py  (Universal Ground-Scene Version)
from __future__ import annotations
from pathlib import Path
import argparse, os, json, base64, csv, datetime as dt

# --------- Service Config (可用环境变量覆盖) ----------
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.chatanywhere.tech/v1")
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # 任意支持图像理解+JSON输出的模型
KEY_FILE        = Path("secrets/.openai_api_key")
GROUND_DIR      = Path("ground/info")

# --------- Core & Extended Schema (通用地面场景) ----------
CORE_SCHEMA_DOC = {
    "object_type": "aircraft|ship|vehicle|facility|infrastructure|crowd|unknown",
    "area": {"type": "polygon|point", "coords": "polygon:[[lon,lat]...闭合] / point:[lon,lat]"},
    "time_utc": "YYYY-MM-DDTHH:MM:SSZ",
    "credibility": "float [0,1]",
    "evidence": [{"type": "photo|doc|url", "uri": "string"}],
    "notes": "≤100字客观说明",
    "provider": "ops_team",
    "schema_version": "1.0"
}

EXTENDED_SCHEMA_DOC = {
    "scene_overview": "一句话总结（如：城市十字路口交通高峰/乡村道路施工/工厂装卸/灾害现场救援）",
    "environment": {"weather": "晴/阴/雨/雪/未知", "lighting": "白天/夜晚/昏暗/未知", "visibility": "好/一般/差/未知"},
    "location_estimate": {"method": "visual|meta|unknown", "geo_known": False, "remark": "坐标来源或未知原因"},
    "entities": [
        {
            "category": "person|vehicle|building|infrastructure|machinery|animal|ship|aircraft|facility|unknown",
            "count": 0,
            "colors": ["颜色词，如 白/黑/红/蓝/灰…"],
            "sizes": "小/中/大/超大 或 约米级",
            "is_moving": None,
            "region": {"type": "bbox_hint|polygon|none", "coords": []},
            "attributes": ["行为或类型标签，如 行走/等候/施工/集会/救援/拥堵/倒塌/冒烟 等"]
        }
    ],
    "orderliness": {"discipline": "有序/一般/混乱", "crowd_density": "无人/稀疏/中等/拥挤", "traffic_flow": "畅通/缓行/拥堵/未知"},
    "activities": ["交通通行/施工/装卸/集会/抗议/巡逻/救援/训练/赛事/节庆/日常经营/未知"],
    "security_presence": {"guards_seen": "true|false|unknown", "checkpoints": "true|false|unknown", "remark": ""},
    "notable_observations": ["异常现象：火焰/烟雾/溢油/倒塌/越界/违停/拥堵/可疑聚集/设备故障 等"],
    "risk_indicators": {"level": "LOW|MEDIUM|HIGH", "reasons": ["触发原因条目"]},
    "investigator_note_cn": "150–300字侦查员视角的客观描述：场景显示了…有…颜色…秩序…人群…机器…值得注意的是… 不得臆测。",
    "uncertainties": ["信息缺失点说明，如 坐标未知/拍摄时间不详/类别判断不确定 等"]
}

DEFAULT_PROMPT = f"""
你是一名现场侦查员。基于给定图像，提取尽可能全面的“地面信息”。适用范围不限于航空/港区，可覆盖城市街道、乡村、交通枢纽、工地、工业园区、公共集会、灾害现场、海岸/内河等任意地面场景。

严格以 JSON 返回，包含“核心字段+扩展字段”。保持客观克制，不得臆造。无法确定的值用 "unknown" 或合理的空结构，并在 uncertainties 说明原因。

【核心字段（必须输出）】
{json.dumps(CORE_SCHEMA_DOC, ensure_ascii=False, indent=2)}

【扩展字段（尽量输出，未知可留空/unknown）】
{json.dumps(EXTENDED_SCHEMA_DOC, ensure_ascii=False, indent=2)}

规则：
1) 仅输出“合法 JSON 对象”，不得包含多余文本、解释或代码块标记。
2) 若无法从图像确定经纬度：area 使用 polygon 的示意方框或 point:[0,0]，并在 location_estimate.remark 说明“坐标未知”。
3) 颜色请用朴素词（白/黑/红/蓝/灰…）。count 不确定可给范围（如 5–8）。
4) investigator_note_cn 用 150–300 字，按“场景显示了…有…颜色…秩序…人群…机器…值得注意的是…”顺序叙述。
"""

# -------------------- Helpers --------------------
def _load_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key and KEY_FILE.exists():
        key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not key:
        raise SystemExit("API key not found. Set OPENAI_API_KEY or create secrets/.openai_api_key")
    return key

def _img_to_data_uri(path: Path) -> str:
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def _client(api_key: str):
    import requests
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    s.base_url = OPENAI_BASE_URL.rstrip("/")
    return s

def _chat_vision(s, model: str, data_uri: str, user_prompt: str) -> dict:
    import json as pyjson
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise data extractor that returns ONLY valid JSON."},
            {"role": "user", "content": [
                {"type": "text", "text": (user_prompt.strip() or DEFAULT_PROMPT)},
                {"type": "image_url", "image_url": {"url": data_uri}}
            ]}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    url = s.base_url + "/chat/completions"
    r = s.post(url, data=pyjson.dumps(payload), timeout=120)
    r.raise_for_status()
    out = r.json()
    txt = out["choices"][0]["message"]["content"]
    return json.loads(txt)

def _validate_and_fix(d: dict) -> dict:
    # 保证核心字段存在；对扩展字段不做强制，但尽量保留原样
    req = ["object_type","area","time_utc","credibility","evidence","notes","provider","schema_version"]
    for k in req:
        d.setdefault(k, "")
    # area 合法化
    area = d.get("area") or {}
    t = (area.get("type") or "point").lower()
    coords = area.get("coords", [0,0] if t=="point" else [])
    if t == "polygon":
        if isinstance(coords, list) and len(coords) >= 3 and coords[0] != coords[-1]:
            coords.append(coords[0])
    d["area"] = {"type": t, "coords": coords}
    # credibility 归一
    try:
        c = float(d.get("credibility", 0.0))
    except Exception:
        c = 0.0
    d["credibility"] = max(0.0, min(1.0, c))
    # evidence 规范
    ev = d.get("evidence", [])
    if not isinstance(ev, list): ev = []
    d["evidence"] = ev
    # schema_version
    d["schema_version"] = "1.0"
    return d

def _flatten_for_csv(rec: dict) -> dict:
    # 将嵌套字段转为字符串，便于 CSV 预览与后续 json.loads
    f = rec.copy()
    for k in ("area","evidence","environment","location_estimate","entities",
              "orderliness","activities","security_presence",
              "notable_observations","risk_indicators","uncertainties"):
        if k in f:
            f[k] = json.dumps(f[k], ensure_ascii=False)
    return f

# -------------------- CLI --------------------
def main():
    ap = argparse.ArgumentParser("Universal Ground Info: image + prompt -> GPT -> JSON/CSV")
    ap.add_argument("--image", required=True, help="本地图片路径（jpg/png）")
    ap.add_argument("--prompt", default="", help="覆盖默认侦查员提示词（可选）")
    ap.add_argument("--provider", default="ops_team", help="写入 provider 字段")
    ap.add_argument("--base_url", default=OPENAI_BASE_URL, help="OpenAI 兼容服务地址")
    ap.add_argument("--model", default=OPENAI_MODEL, help="模型名")
    args = ap.parse_args()

    img = Path(args.image).expanduser().resolve()
    if not img.exists():
        raise SystemExit(f"Image not found: {img}")

    GROUND_DIR.mkdir(parents=True, exist_ok=True)

    os.environ["OPENAI_BASE_URL"] = args.base_url
    api_key = _load_api_key()
    s = _client(api_key)

    data_uri = _img_to_data_uri(img)
    rec = _chat_vision(s, args.model, data_uri, args.prompt)
    rec = _validate_and_fix(rec)
    if args.provider:
        rec["provider"] = args.provider

    ts = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    json_path = GROUND_DIR / f"ground_info_gpt_{ts}.json"
    csv_path  = GROUND_DIR / f"ground_info_gpt_{ts}.csv"

    json_path.write_text(json.dumps([rec], ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(_flatten_for_csv(rec).keys()))
        w.writeheader(); w.writerow(_flatten_for_csv(rec))

    print("[OK] JSON:", json_path)
    print("[OK] CSV :", csv_path)

if __name__ == "__main__":
    main()



'''
# 1) 可选：安全保存密钥（运行后粘贴你的新密钥；文件会被 chmod 600）
python save_key.py

# 2) 执行（使用你给的 base_url）
python create_ground_from_gpt.py \
  --image ./image/origin/boats.jpg \
  --base_url https://api.chatanywhere.tech/v1 \
  --model gpt-4o-mini

  project_root/
├─ ground/
│  └─ info/                      # GPT 生成的地面信息会写在这里
├─ secrets/
│  └─ .openai_api_key            # 本地密钥文件（600 权限）
├─ create_ground_from_gpt.py     # 主脚本：图像+prompt → GPT → JSON/CSV
└─ save_key.py                   # 可选：把密钥安全写入 secrets/.openai_api_key

Demo
{
  "object_type": "vehicle",
  "area": {"type":"polygon","coords":[[0,0],[1,0],[1,1],[0,1],[0,0]]},
  "time_utc": "2025-09-26T02:00:00Z",
  "credibility": 0.8,
  "evidence": [{"type":"photo","uri":"local://traffic.jpg"}],
  "notes": "图像显示城市十字路口，车辆密集，人行道上有人群。",
  "provider": "ops_team",
  "schema_version": "1.0",

  "scene_overview": "城市主干道十字路口交通高峰。",
  "environment": {"weather":"晴","lighting":"白天","visibility":"好"},
  "location_estimate": {"method":"visual","geo_known":false,"remark":"缺乏显式坐标"},
  "entities": [
    {"category":"vehicle","count":15,"colors":["白","黑","灰","红"],"sizes":"小-中型","is_moving":true,"region":{"type":"bbox_hint","coords":[]},"attributes":["轿车","公交车","摩托车"]},
    {"category":"person","count":20,"colors":["深色衣物","浅色衣物"],"sizes":"小","is_moving":true,"region":{"type":"bbox_hint","coords":[]},"attributes":["等候红灯","行走"]}
  ],
  "orderliness": {"discipline":"较有序","crowd_density":"中等","traffic_flow":"拥堵"},
  "activities": ["交通通行","行人过街"],
  "security_presence": {"guards_seen":"false","checkpoints":"unknown","remark":"未见明显执勤人员"},
  "notable_observations": ["部分车辆违规压线","行人集中等待"],
  "risk_indicators": {"level":"MEDIUM","reasons":["交通拥堵","违规行为存在"]},
  "investigator_note_cn": "场景显示一个城市十字路口，车辆以白色、黑色和红色为主，数量较多，部分处于停滞状态，整体秩序尚可但存在拥堵。人群分布在人行道与过街区域，衣着颜色各异，多为深浅色系。机器设备方面可见公交车、摩托车在道路上穿插。秩序上交通灯有效运行，但仍有个别车辆压线或抢行。值得注意的是人流量较大，若持续增加可能影响安全。总体来看场景较为繁忙但在可控范围。",
  "uncertainties": ["未能获取具体地理坐标","无法确认拍摄具体时间"]
}

'''