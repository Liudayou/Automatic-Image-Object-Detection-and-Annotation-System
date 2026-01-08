"""
导出功能 API
"""
import os
import uuid
import zipfile
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse

from app.config import settings
from app.models import ExportRequest, ExportFormat
from app.services.annotation import annotation_service

router = APIRouter()


@router.post("/")
async def export_annotations(request: ExportRequest):
    """
    导出标注数据
    """
    try:
        result = annotation_service.export_annotations(
            image_ids=request.image_ids,
            format=request.format
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def export_and_download(
    request: ExportRequest,
    background_tasks: BackgroundTasks
):
    """
    导出标注并下载为ZIP文件
    """
    try:
        # 创建临时导出目录
        export_id = str(uuid.uuid4())[:8]
        export_dir = Path(settings.EXPORT_DIR) / f"export_{export_id}"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # 导出标注
        result = annotation_service.export_annotations(
            image_ids=request.image_ids,
            format=request.format,
            output_dir=str(export_dir)
        )
        
        # 如果需要包含图像
        if request.include_images:
            images_dir = export_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            for image_id in request.image_ids:
                data = annotation_service.get_annotations(image_id)
                if data and data.get("image_path"):
                    src_path = Path(settings.UPLOAD_DIR).parent / data["image_path"].lstrip("/")
                    if src_path.exists():
                        shutil.copy(src_path, images_dir / src_path.name)
        
        # 创建 ZIP 文件
        zip_path = Path(settings.EXPORT_DIR) / f"export_{export_id}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in export_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(export_dir)
                    zipf.write(file_path, arcname)
        
        # 清理临时目录
        background_tasks.add_task(shutil.rmtree, export_dir)
        
        return FileResponse(
            path=str(zip_path),
            filename=f"annotations_{request.format.value}_{export_id}.zip",
            media_type="application/zip"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def get_export_formats():
    """
    获取支持的导出格式
    """
    return {
        "formats": [
            {"value": "yolo", "label": "YOLO (TXT)", "description": "YOLO格式标注文件"},
            {"value": "coco", "label": "COCO (JSON)", "description": "COCO数据集格式"},
            {"value": "voc", "label": "Pascal VOC (XML)", "description": "Pascal VOC XML格式"},
            {"value": "json", "label": "JSON", "description": "原始JSON格式"}
        ]
    }


@router.delete("/clean")
async def clean_exports():
    """
    清理导出目录
    """
    export_path = Path(settings.EXPORT_DIR)
    count = 0
    
    for item in export_path.iterdir():
        if item.is_file():
            item.unlink()
            count += 1
        elif item.is_dir():
            shutil.rmtree(item)
            count += 1
    
    return {"success": True, "cleaned_items": count}
