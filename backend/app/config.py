"""
系统配置文件
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
YOLOV5_DIR = BASE_DIR / "yolov5"
DATASET_DIR = BASE_DIR / "dataset"

@dataclass
class Settings:
    """应用配置"""
    # 应用信息
    APP_NAME: str = "自动图像目标检测与标注系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 文件上传配置
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # 模型配置
    WEIGHTS_DIR: str = str(YOLOV5_DIR / "weights")
    DEFAULT_WEIGHTS: str = "yolov5s.pt"
    DEVICE: str = "cuda:0"  # 或 "cpu"
    CONF_THRESHOLD: float = 0.25
    IOU_THRESHOLD: float = 0.45
    IMG_SIZE: int = 640
    
    # 数据集配置
    COCO_DIR: str = str(DATASET_DIR / "coco")
    VOC_DIR: str = str(DATASET_DIR / "VOC")
    CUSTOM_DATASET_DIR: str = str(BASE_DIR / "custom_datasets")
    
    # 标注导出配置
    EXPORT_DIR: str = str(BASE_DIR / "exports")
    
    # 训练配置
    TRAIN_OUTPUT_DIR: str = str(YOLOV5_DIR / "runs" / "train")
    DETECT_OUTPUT_DIR: str = str(YOLOV5_DIR / "runs" / "detect")
    
    # 数据库配置
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/database.db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    # 图像类型 (使用 field 定义列表默认值)
    ALLOWED_IMAGE_TYPES: List[str] = field(default_factory=lambda: ["image/jpeg", "image/png", "image/bmp", "image/webp"])
    ALLOWED_VIDEO_TYPES: List[str] = field(default_factory=lambda: ["video/mp4", "video/avi", "video/mov", "video/mkv"])

settings = Settings()

# 确保必要目录存在
for dir_path in [settings.UPLOAD_DIR, settings.EXPORT_DIR, settings.CUSTOM_DATASET_DIR]:
    os.makedirs(dir_path, exist_ok=True)
