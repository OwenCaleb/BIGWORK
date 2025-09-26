from ultralytics.utils import SETTINGS
from ultralytics import YOLO

# 设定目录（本进程立即生效，并写入全局配置）
SETTINGS.update({
    "datasets_dir": "/home/liwenbo/projects/School/BIGWORK/data/datasets",
    "weights_dir":  "/home/liwenbo/projects/School/BIGWORK/data/weights",
    "runs_dir":     "/home/liwenbo/projects/School/BIGWORK/data/runs",
})

# 训练：会自动把 DOTA8 拉到 /data/obb_datasets/dota8
model = YOLO("yolo11n-obb.pt")
model.train(task="obb", data="dota8.yaml", imgsz=1024, epochs=50)

# 验证 / 推理
model.val(task="obb", data="dota8.yaml")
model.predict(task="obb", source="your_image.jpg", save=True)
