"""
数据预处理 API
"""
import os
import uuid
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from PIL import Image, ImageEnhance, ImageFilter

from app.config import settings
from app.models import PreprocessingConfig

router = APIRouter()


def cv2_imread(image_path: str, flags=cv2.IMREAD_COLOR):
    """
    读取图像，支持中文路径
    """
    # 使用 numpy 读取文件，避免中文路径问题
    img_array = np.fromfile(image_path, dtype=np.uint8)
    img = cv2.imdecode(img_array, flags)
    return img


def calculate_blur_score(image_path: str) -> float:
    """计算图像模糊度分数（拉普拉斯方差）"""
    img = cv2_imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    return cv2.Laplacian(img, cv2.CV_64F).var()


@router.post("/augment")
async def augment_image(
    file: UploadFile = File(..., description="要增强的图像"),
    resize_width: Optional[int] = Form(None, description="调整宽度"),
    resize_height: Optional[int] = Form(None, description="调整高度"),
    rotate: Optional[float] = Form(None, description="旋转角度"),
    flip_horizontal: bool = Form(False, description="水平翻转"),
    flip_vertical: bool = Form(False, description="垂直翻转"),
    brightness: Optional[float] = Form(None, description="亮度 (0.5-2.0)"),
    contrast: Optional[float] = Form(None, description="对比度 (0.5-2.0)"),
    saturation: Optional[float] = Form(None, description="饱和度 (0.5-2.0)"),
    hue_shift: Optional[int] = Form(None, description="色调偏移 (-180-180)")
):
    """
    对图像进行数据增强
    """
    # 保存原始文件
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    
    original_path = Path(settings.UPLOAD_DIR) / "temp" / f"{file_id}_original{file_ext}"
    augmented_path = Path(settings.UPLOAD_DIR) / "augmented" / f"{file_id}_augmented{file_ext}"
    
    original_path.parent.mkdir(parents=True, exist_ok=True)
    augmented_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 保存上传文件
        content = await file.read()
        with open(original_path, "wb") as f:
            f.write(content)
        
        # 打开图像
        img = Image.open(original_path)
        
        # 调整大小
        if resize_width and resize_height:
            img = img.resize((resize_width, resize_height), Image.Resampling.LANCZOS)
        elif resize_width:
            ratio = resize_width / img.width
            img = img.resize((resize_width, int(img.height * ratio)), Image.Resampling.LANCZOS)
        elif resize_height:
            ratio = resize_height / img.height
            img = img.resize((int(img.width * ratio), resize_height), Image.Resampling.LANCZOS)
        
        # 旋转
        if rotate:
            img = img.rotate(rotate, expand=True, fillcolor=(128, 128, 128))
        
        # 翻转
        if flip_horizontal:
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if flip_vertical:
            img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        
        # 亮度调整
        if brightness:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
        
        # 对比度调整
        if contrast:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
        
        # 饱和度调整
        if saturation:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(saturation)
        
        # 色调偏移 (使用OpenCV)
        if hue_shift:
            img_array = np.array(img)
            img_hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            img_hsv[:, :, 0] = (img_hsv[:, :, 0].astype(int) + hue_shift) % 180
            img_array = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2RGB)
            img = Image.fromarray(img_array)
        
        # 保存增强后的图像
        img.save(augmented_path)
        
        # 清理原始临时文件
        original_path.unlink()
        
        return {
            "success": True,
            "original_size": {"width": Image.open(original_path if original_path.exists() else augmented_path).width, 
                            "height": Image.open(augmented_path).height},
            "augmented_size": {"width": img.width, "height": img.height},
            "augmented_path": f"/uploads/augmented/{file_id}_augmented{file_ext}"
        }
        
    except Exception as e:
        # 清理文件
        if original_path.exists():
            original_path.unlink()
        if augmented_path.exists():
            augmented_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-augment")
async def batch_augment(
    files: List[UploadFile] = File(..., description="要增强的图像列表"),
    operations: str = Form(..., description="增强操作配置JSON")
):
    """
    批量图像增强
    """
    import json
    
    try:
        config = json.loads(operations)
    except:
        raise HTTPException(status_code=400, detail="无效的操作配置JSON")
    
    results = []
    augmented_dir = Path(settings.UPLOAD_DIR) / "augmented"
    augmented_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        try:
            file_id = str(uuid.uuid4())
            file_ext = Path(file.filename).suffix
            
            content = await file.read()
            img = Image.open(content)
            
            # 应用配置的增强操作
            if config.get("resize"):
                img = img.resize(tuple(config["resize"]), Image.Resampling.LANCZOS)
            
            if config.get("rotate"):
                img = img.rotate(config["rotate"], expand=True)
            
            if config.get("flip_horizontal"):
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            
            if config.get("brightness"):
                img = ImageEnhance.Brightness(img).enhance(config["brightness"])
            
            if config.get("contrast"):
                img = ImageEnhance.Contrast(img).enhance(config["contrast"])
            
            save_path = augmented_dir / f"{file_id}{file_ext}"
            img.save(save_path)
            
            results.append({
                "original_name": file.filename,
                "augmented_path": f"/uploads/augmented/{file_id}{file_ext}",
                "success": True
            })
            
        except Exception as e:
            results.append({
                "original_name": file.filename,
                "error": str(e),
                "success": False
            })
    
    return {"results": results, "total": len(results)}


@router.post("/quality-check")
async def check_image_quality(
    file: UploadFile = File(..., description="要检查的图像"),
    blur_threshold: float = Form(100.0, description="模糊度阈值")
):
    """
    检查图像质量（模糊度检测）
    """
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    temp_path = Path(settings.UPLOAD_DIR) / "temp" / f"{file_id}{file_ext}"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        blur_score = calculate_blur_score(str(temp_path))
        is_blurry = blur_score < blur_threshold
        
        # 获取图像信息
        img = Image.open(temp_path)
        
        result = {
            "filename": file.filename,
            "blur_score": round(blur_score, 2),
            "blur_threshold": blur_threshold,
            "is_blurry": is_blurry,
            "quality": "低" if is_blurry else "正常",
            "image_info": {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode
            }
        }
        
        temp_path.unlink()
        return result
        
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-quality-check")
async def batch_quality_check(
    files: List[UploadFile] = File(..., description="要检查的图像列表"),
    blur_threshold: float = Form(100.0, description="模糊度阈值")
):
    """
    批量图像质量检查
    """
    results = []
    temp_dir = Path(settings.UPLOAD_DIR) / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        temp_path = temp_dir / f"{file_id}{file_ext}"
        
        try:
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)
            
            blur_score = calculate_blur_score(str(temp_path))
            is_blurry = blur_score < blur_threshold
            
            results.append({
                "filename": file.filename,
                "blur_score": round(blur_score, 2),
                "is_blurry": is_blurry,
                "quality": "低" if is_blurry else "正常"
            })
            
            temp_path.unlink()
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e)
            })
            if temp_path.exists():
                temp_path.unlink()
    
    # 统计
    blurry_count = sum(1 for r in results if r.get("is_blurry", False))
    
    return {
        "results": results,
        "total": len(results),
        "blurry_count": blurry_count,
        "quality_rate": round((len(results) - blurry_count) / len(results) * 100, 2) if results else 0
    }
