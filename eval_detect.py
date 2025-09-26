from pathlib import Path
import argparse
from ultralytics import YOLO
from ultralytics.utils import ASSETS

'''
python eval_detect.py --weights ./data/runs/obb/train/weights/best.pt --image image/origin/boats.jpg 
python eval_detect.py --weights ./yolo11n-obb.pt  --image image/origin/boats.jpg 
'''
def pick_image(user_img: str | None) -> Path:
    # 1) 用户指定
    if user_img:
        p = Path(user_img).expanduser().resolve()
        if p.exists():
            return p

    # 2) 已下载的 DOTA8 验证集（按你前面设置的目录推测）
    candidates = [
        Path("/home/liwenbo/projects/School/BIGWORK/data/obb_datasets/dota8/images/val"),
        Path("/home/liwenbo/projects/School/BIGWORK/data/datasets/dota8/images/val"),
    ]
    for d in candidates:
        if d.exists():
            imgs = sorted([p for p in d.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}])
            if imgs:
                return imgs[0]

    # 3) Ultralytics 自带示例图
    # （包里一般有 bus.jpg / zidane.jpg / truck.jpg 等）
    bus = ASSETS / "bus.jpg"
    if bus.exists():
        return bus

    raise FileNotFoundError("未找到可用的测试图片，请手动用 --image 指定一张本地图片。")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default="./yolo11n-obb.pt", help="本地权重路径（例如 best.pt 或 yolo11n-obb.pt）")
    ap.add_argument("--image", default="", help="本地测试图片路径（可选）")
    ap.add_argument("--outdir", default="./image", help="输出根目录")
    ap.add_argument("--name", default="pred_demo", help="输出子目录名")
    ap.add_argument("--imgsz", type=int, default=1024)
    args = ap.parse_args()

    # 模型（必须是本地文件，避免联网下载）
    w = Path(args.weights).expanduser().resolve()
    if not w.exists():
        raise FileNotFoundError(f"找不到本地权重：{w} ；请改成你的 best.pt 或把官方 yolo11n-obb.pt 放到当前目录。")

    model = YOLO(str(w))

    # 选图（不走网络）
    img_path = pick_image(args.image)
    print(f"[INFO] 使用测试图片：{img_path}")

    # 预测
    results = model.predict(
        source=str(img_path),
        task="obb",
        imgsz=args.imgsz,
        save=True,
        project=str(Path(args.outdir)),
        name=args.name,
        exist_ok=True,
        show=False
    )

    r0 = results[0]
    print(f"[INFO] 检测到 {len(r0.obb)} 个框；输出目录：{r0.save_dir}")
    # 访问结果字段
    xywhr = r0.obb.xywhr
    xyxyxyxy = r0.obb.xyxyxyxy
    names = [r0.names[int(c)] for c in r0.obb.cls.int()]
    confs = r0.obb.conf
    print("[DEBUG] 类别样例：", names[:5], "  置信样例：", [round(float(x),3) for x in confs[:5]])

if __name__ == "__main__":
    main()
