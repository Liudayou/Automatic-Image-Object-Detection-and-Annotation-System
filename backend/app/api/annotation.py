"""
标注管理 API
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models import AnnotationSaveRequest, Annotation, BoundingBox
from app.services.annotation import annotation_service

router = APIRouter()


@router.post("/save")
async def save_annotations(request: AnnotationSaveRequest):
    """
    保存标注数据
    """
    try:
        result = annotation_service.save_annotations(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{image_id}")
async def get_annotations(image_id: str):
    """
    获取指定图像的标注数据
    """
    data = annotation_service.get_annotations(image_id)
    if data is None:
        raise HTTPException(status_code=404, detail="标注数据不存在")
    return data


@router.delete("/{image_id}")
async def delete_annotations(image_id: str):
    """
    删除标注数据
    """
    success = annotation_service.delete_annotations(image_id)
    if not success:
        raise HTTPException(status_code=404, detail="标注数据不存在")
    return {"success": True, "message": "标注已删除"}


@router.get("/")
async def list_annotations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    列出所有标注
    """
    all_annotations = annotation_service.list_annotations()
    
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_annotations[start:end]
    
    return {
        "items": paginated,
        "total": len(all_annotations),
        "page": page,
        "page_size": page_size
    }


@router.put("/{image_id}/annotation/{annotation_id}")
async def update_annotation(
    image_id: str,
    annotation_id: int,
    annotation: Annotation
):
    """
    更新单个标注
    """
    data = annotation_service.get_annotations(image_id)
    if data is None:
        raise HTTPException(status_code=404, detail="标注数据不存在")
    
    # 找到并更新指定标注
    found = False
    for i, ann in enumerate(data["annotations"]):
        if ann["id"] == annotation_id:
            data["annotations"][i] = annotation.dict()
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail="标注不存在")
    
    # 保存更新
    from datetime import datetime
    data["updated_at"] = datetime.now().isoformat()
    
    request = AnnotationSaveRequest(
        image_id=data["image_id"],
        image_path=data["image_path"],
        image_width=data["image_width"],
        image_height=data["image_height"],
        annotations=[Annotation(**ann) for ann in data["annotations"]]
    )
    
    annotation_service.save_annotations(request)
    return {"success": True, "message": "标注已更新"}


@router.delete("/{image_id}/annotation/{annotation_id}")
async def delete_single_annotation(image_id: str, annotation_id: int):
    """
    删除单个标注
    """
    data = annotation_service.get_annotations(image_id)
    if data is None:
        raise HTTPException(status_code=404, detail="标注数据不存在")
    
    # 过滤掉要删除的标注
    original_count = len(data["annotations"])
    data["annotations"] = [
        ann for ann in data["annotations"] if ann["id"] != annotation_id
    ]
    
    if len(data["annotations"]) == original_count:
        raise HTTPException(status_code=404, detail="标注不存在")
    
    # 保存更新
    from datetime import datetime
    data["updated_at"] = datetime.now().isoformat()
    
    request = AnnotationSaveRequest(
        image_id=data["image_id"],
        image_path=data["image_path"],
        image_width=data["image_width"],
        image_height=data["image_height"],
        annotations=[Annotation(**ann) for ann in data["annotations"]]
    )
    
    annotation_service.save_annotations(request)
    return {"success": True, "message": "标注已删除"}


@router.post("/{image_id}/annotation")
async def add_annotation(image_id: str, annotation: Annotation):
    """
    添加新标注
    """
    data = annotation_service.get_annotations(image_id)
    if data is None:
        raise HTTPException(status_code=404, detail="标注数据不存在")
    
    # 生成新ID
    max_id = max([ann["id"] for ann in data["annotations"]], default=0)
    annotation.id = max_id + 1
    annotation.is_manual = True
    
    data["annotations"].append(annotation.dict())
    
    # 保存更新
    from datetime import datetime
    data["updated_at"] = datetime.now().isoformat()
    
    request = AnnotationSaveRequest(
        image_id=data["image_id"],
        image_path=data["image_path"],
        image_width=data["image_width"],
        image_height=data["image_height"],
        annotations=[Annotation(**ann) for ann in data["annotations"]]
    )
    
    annotation_service.save_annotations(request)
    return {"success": True, "annotation": annotation, "message": "标注已添加"}
