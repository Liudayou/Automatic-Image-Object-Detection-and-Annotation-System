"""
Pydantic 数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class BoundingBox(BaseModel):
    """边界框模型"""
    x: float = Field(..., description="左上角x坐标")
    y: float = Field(..., description="左上角y坐标")
    width: float = Field(..., description="边界框宽度")
    height: float = Field(..., description="边界框高度")


class Detection(BaseModel):
    """单个检测结果"""
    id: int = Field(..., description="检测ID")
    class_id: int = Field(..., description="类别ID")
    class_name: str = Field(..., description="类别名称")
    confidence: float = Field(..., description="置信度")
    bbox: BoundingBox = Field(..., description="边界框")


class DetectionRequest(BaseModel):
    """检测请求参数"""
    conf_threshold: float = Field(0.25, ge=0, le=1, description="置信度阈值")
    iou_threshold: float = Field(0.45, ge=0, le=1, description="IOU阈值")
    img_size: int = Field(640, description="推理图像尺寸")
    weights: str = Field("yolov5s.pt", description="模型权重文件")
    classes: Optional[List[int]] = Field(None, description="要检测的类别ID列表")


class DetectionResult(BaseModel):
    """检测结果响应"""
    image_id: str = Field(..., description="图像ID")
    image_path: str = Field(..., description="图像路径")
    image_width: int = Field(..., description="图像宽度")
    image_height: int = Field(..., description="图像高度")
    detections: List[Detection] = Field(default=[], description="检测结果列表")
    inference_time: float = Field(..., description="推理时间(ms)")


class Annotation(BaseModel):
    """标注数据模型"""
    id: int = Field(..., description="标注ID")
    class_id: int = Field(..., description="类别ID")
    class_name: str = Field(..., description="类别名称")
    bbox: BoundingBox = Field(..., description="边界框")
    is_manual: bool = Field(False, description="是否为手动标注")
    confidence: Optional[float] = Field(None, description="置信度（自动检测时）")


class AnnotationSaveRequest(BaseModel):
    """保存标注请求"""
    image_id: str = Field(..., description="图像ID")
    image_path: str = Field(..., description="图像路径")
    image_width: int = Field(..., description="图像宽度")
    image_height: int = Field(..., description="图像高度")
    annotations: List[Annotation] = Field(..., description="标注列表")


class ExportFormat(str, Enum):
    """导出格式枚举"""
    YOLO = "yolo"
    COCO = "coco"
    VOC = "voc"
    JSON = "json"


class ExportRequest(BaseModel):
    """导出请求"""
    image_ids: List[str] = Field(..., description="要导出的图像ID列表")
    format: ExportFormat = Field(ExportFormat.YOLO, description="导出格式")
    include_images: bool = Field(False, description="是否包含图像文件")


class TrainingConfig(BaseModel):
    """训练配置"""
    weights: str = Field("yolov5s.pt", description="预训练权重")
    data_yaml: str = Field(..., description="数据集配置文件路径")
    epochs: int = Field(100, ge=1, description="训练轮数")
    batch_size: int = Field(16, ge=1, description="批次大小")
    img_size: int = Field(640, description="训练图像尺寸")
    learning_rate: float = Field(0.01, gt=0, description="学习率")
    project: str = Field("runs/train", description="输出目录")
    name: str = Field("exp", description="实验名称")
    device: str = Field("", description="训练设备")
    workers: int = Field(8, ge=0, description="数据加载线程数")
    patience: int = Field(100, ge=0, description="早停耐心值")
    optimizer: str = Field("SGD", description="优化器")


class TrainingStatus(BaseModel):
    """训练状态"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="状态")
    progress: float = Field(0, ge=0, le=100, description="进度百分比")
    current_epoch: int = Field(0, description="当前轮数")
    total_epochs: int = Field(0, description="总轮数")
    metrics: Optional[Dict[str, Any]] = Field(None, description="训练指标")
    message: Optional[str] = Field(None, description="状态消息")


class EvaluationResult(BaseModel):
    """评估结果"""
    mAP50: float = Field(..., description="mAP@0.5")
    mAP50_95: float = Field(..., description="mAP@0.5:0.95")
    precision: float = Field(..., description="精确率")
    recall: float = Field(..., description="召回率")
    f1_score: float = Field(..., description="F1分数")
    class_metrics: Optional[Dict[str, Dict[str, float]]] = Field(None, description="各类别指标")


class PreprocessingConfig(BaseModel):
    """预处理配置"""
    resize: Optional[tuple] = Field(None, description="调整大小 (width, height)")
    crop: Optional[Dict[str, int]] = Field(None, description="裁剪参数")
    rotate: Optional[float] = Field(None, description="旋转角度")
    flip_horizontal: bool = Field(False, description="水平翻转")
    flip_vertical: bool = Field(False, description="垂直翻转")
    brightness: Optional[float] = Field(None, description="亮度调整")
    contrast: Optional[float] = Field(None, description="对比度调整")
    saturation: Optional[float] = Field(None, description="饱和度调整")
    hue: Optional[float] = Field(None, description="色调调整")
    blur_threshold: Optional[float] = Field(None, description="模糊检测阈值")


class DatasetInfo(BaseModel):
    """数据集信息"""
    name: str = Field(..., description="数据集名称")
    path: str = Field(..., description="数据集路径")
    num_images: int = Field(..., description="图像数量")
    num_classes: int = Field(..., description="类别数量")
    classes: List[str] = Field(..., description="类别列表")
    split: Dict[str, int] = Field(..., description="数据集划分")


class ClassInfo(BaseModel):
    """类别信息"""
    id: int = Field(..., description="类别ID")
    name: str = Field(..., description="类别名称")
    color: str = Field(..., description="显示颜色")


# COCO 80类默认配置
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
    "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]

# 生成类别颜色
def generate_colors(n):
    """生成n个不同的颜色"""
    import colorsys
    colors = []
    for i in range(n):
        hue = i / n
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
        )
        colors.append(hex_color)
    return colors

COCO_COLORS = generate_colors(len(COCO_CLASSES))

def get_class_info() -> List[ClassInfo]:
    """获取类别信息列表"""
    return [
        ClassInfo(id=i, name=name, color=COCO_COLORS[i])
        for i, name in enumerate(COCO_CLASSES)
    ]
