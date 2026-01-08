"""
目标检测 API
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import DetectionRequest, DetectionResult, get_class_info
from app.services.detector import detector

router = APIRouter()


@router.post("/detect", response_model=DetectionResult)
async def detect_image(
    file: UploadFile = File(..., description="要检测的图像文件"),
    conf_threshold: float = Form(0.25, description="置信度阈值"),
    iou_threshold: float = Form(0.45, description="IOU阈值"),
    img_size: int = Form(640, description="推理图像尺寸"),
    weights: str = Form("yolov5s.pt", description="模型权重"),
    classes: Optional[str] = Form(None, description="类别ID列表，逗号分隔")
):
    """
    对上传的图像进行目标检测
    """
    # 验证文件类型
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}"
        )
    
    # 保存上传文件
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    save_path = Path(settings.UPLOAD_DIR) / "images" / f"{file_id}{file_ext}"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 解析类别列表
        class_list = None
        if classes:
            class_list = [int(c.strip()) for c in classes.split(",")]
        
        # 执行检测
        result = detector.detect(
            image_path=str(save_path),
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            img_size=img_size,
            weights=weights,
            classes=class_list
        )
        
        # 更新图像路径为相对路径（用于前端访问）
        result.image_path = f"/uploads/images/{file_id}{file_ext}"
        
        return result
        
    except Exception as e:
        # 清理文件
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect/batch")
async def detect_images_batch(
    files: List[UploadFile] = File(..., description="要检测的图像文件列表"),
    conf_threshold: float = Form(0.25),
    iou_threshold: float = Form(0.45),
    img_size: int = Form(640),
    weights: str = Form("yolov5s.pt")
):
    """
    批量目标检测
    """
    results = []
    
    for file in files:
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            continue
        
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        save_path = Path(settings.UPLOAD_DIR) / "images" / f"{file_id}{file_ext}"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(save_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            result = detector.detect(
                image_path=str(save_path),
                conf_threshold=conf_threshold,
                iou_threshold=iou_threshold,
                img_size=img_size,
                weights=weights
            )
            
            result.image_path = f"/uploads/images/{file_id}{file_ext}"
            results.append(result)
            
        except Exception as e:
            results.append({
                "error": str(e),
                "filename": file.filename
            })
    
    return {"results": results, "total": len(results)}


@router.post("/detect/url")
async def detect_from_url(
    image_url: str = Form(..., description="图像URL"),
    conf_threshold: float = Form(0.25),
    iou_threshold: float = Form(0.45),
    img_size: int = Form(640),
    weights: str = Form("yolov5s.pt")
):
    """
    从URL检测图像
    """
    import urllib.request
    
    file_id = str(uuid.uuid4())
    # 从URL获取扩展名
    url_path = Path(image_url.split("?")[0])
    file_ext = url_path.suffix or ".jpg"
    save_path = Path(settings.UPLOAD_DIR) / "images" / f"{file_id}{file_ext}"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 下载图像
        urllib.request.urlretrieve(image_url, str(save_path))
        
        result = detector.detect(
            image_path=str(save_path),
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            img_size=img_size,
            weights=weights
        )
        
        result.image_path = f"/uploads/images/{file_id}{file_ext}"
        return result
        
    except Exception as e:
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weights")
async def get_available_weights():
    """获取可用的模型权重列表"""
    weights = detector.get_available_weights()
    return {"weights": weights}


@router.get("/classes")
async def get_classes():
    """获取支持的目标类别列表"""
    return {"classes": get_class_info()}


@router.get("/model/info")
async def get_model_info(weights: str = Query("yolov5s.pt")):
    """获取模型信息"""
    try:
        info = detector.get_model_info(weights)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
