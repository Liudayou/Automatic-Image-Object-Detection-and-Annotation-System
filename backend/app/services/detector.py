"""
YOLOv5 检测服务
"""
import sys
import time
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np
import torch
from PIL import Image

# 确保 yolov5 在路径中
YOLOV5_PATH = Path(__file__).resolve().parent.parent.parent.parent / "yolov5"
if str(YOLOV5_PATH) not in sys.path:
    sys.path.insert(0, str(YOLOV5_PATH))

from app.config import settings
from app.models import Detection, BoundingBox, DetectionResult, COCO_CLASSES


class YOLOv5Detector:
    """YOLOv5 检测器封装"""
    
    _instance = None
    _models: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.device = self._get_device()
    
    def _get_device(self) -> str:
        """获取可用设备"""
        if settings.DEVICE.startswith("cuda") and torch.cuda.is_available():
            return settings.DEVICE
        return "cpu"
    
    def load_model(self, weights: str = None) -> Any:
        """加载模型"""
        if weights is None:
            weights = settings.DEFAULT_WEIGHTS
        
        # 检查模型是否已加载
        if weights in self._models:
            return self._models[weights]
        
        # 构建权重路径
        if not Path(weights).is_absolute():
            # 首先检查 yolov5 根目录
            weights_path = YOLOV5_PATH / weights
            if not weights_path.exists():
                # 检查 weights 目录
                weights_path = YOLOV5_PATH / "weights" / weights
        else:
            weights_path = Path(weights)
        
        if not weights_path.exists():
            raise FileNotFoundError(f"权重文件不存在: {weights_path}")
        
        # 使用 torch.hub 加载模型
        model = torch.hub.load(
            str(YOLOV5_PATH),
            'custom',
            path=str(weights_path),
            source='local',
            device=self.device
        )
        
        self._models[weights] = model
        return model
    
    def detect(
        self,
        image_path: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        img_size: int = 640,
        weights: str = None,
        classes: Optional[List[int]] = None
    ) -> DetectionResult:
        """
        执行目标检测
        
        Args:
            image_path: 图像路径
            conf_threshold: 置信度阈值
            iou_threshold: IOU阈值
            img_size: 推理图像尺寸
            weights: 模型权重
            classes: 要检测的类别列表
            
        Returns:
            DetectionResult: 检测结果
        """
        start_time = time.time()
        
        # 加载模型
        model = self.load_model(weights)
        
        # 设置模型参数
        model.conf = conf_threshold
        model.iou = iou_threshold
        if classes:
            model.classes = classes
        
        # 读取图像获取尺寸
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # 执行推理
        results = model(image_path, size=img_size)
        
        # 解析结果
        detections = []
        pred = results.pandas().xyxy[0]  # 获取预测结果
        
        for idx, row in pred.iterrows():
            x1, y1, x2, y2 = row['xmin'], row['ymin'], row['xmax'], row['ymax']
            
            detection = Detection(
                id=idx,
                class_id=int(row['class']),
                class_name=row['name'],
                confidence=float(row['confidence']),
                bbox=BoundingBox(
                    x=float(x1),
                    y=float(y1),
                    width=float(x2 - x1),
                    height=float(y2 - y1)
                )
            )
            detections.append(detection)
        
        inference_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        # 生成图像ID
        image_id = str(uuid.uuid4())
        
        return DetectionResult(
            image_id=image_id,
            image_path=image_path,
            image_width=img_width,
            image_height=img_height,
            detections=detections,
            inference_time=round(inference_time, 2)
        )
    
    def detect_batch(
        self,
        image_paths: List[str],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        img_size: int = 640,
        weights: str = None,
        classes: Optional[List[int]] = None
    ) -> List[DetectionResult]:
        """批量检测"""
        results = []
        for path in image_paths:
            result = self.detect(
                path, conf_threshold, iou_threshold, 
                img_size, weights, classes
            )
            results.append(result)
        return results
    
    def get_available_weights(self) -> List[str]:
        """获取可用的权重文件列表"""
        weights = []
        
        # 检查 yolov5 根目录
        for pt_file in YOLOV5_PATH.glob("*.pt"):
            weights.append(pt_file.name)
        
        # 检查 weights 目录
        weights_dir = YOLOV5_PATH / "weights"
        if weights_dir.exists():
            for pt_file in weights_dir.glob("*.pt"):
                weights.append(pt_file.name)
        
        return list(set(weights))
    
    def get_model_info(self, weights: str = None) -> Dict[str, Any]:
        """获取模型信息"""
        model = self.load_model(weights)
        return {
            "weights": weights or settings.DEFAULT_WEIGHTS,
            "device": str(self.device),
            "num_classes": len(model.names),
            "class_names": model.names,
        }


# 全局检测器实例
detector = YOLOv5Detector()
