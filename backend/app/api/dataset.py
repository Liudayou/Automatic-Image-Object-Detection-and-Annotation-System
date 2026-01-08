"""
数据集管理 API
"""
import os
import yaml
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings, YOLOV5_DIR, DATASET_DIR
from app.models import DatasetInfo

router = APIRouter()


@router.get("/list")
async def list_datasets():
    """
    列出所有可用数据集
    """
    datasets = []
    
    # 检查 COCO 数据集
    coco_yaml = DATASET_DIR / "coco" / "coco.yaml"
    if coco_yaml.exists():
        with open(coco_yaml, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            datasets.append({
                "name": "COCO",
                "path": str(coco_yaml),
                "type": "coco",
                "classes": config.get("names", []),
                "num_classes": config.get("nc", 0)
            })
    
    # 检查 VOC 数据集
    voc_yaml = YOLOV5_DIR / "data" / "VOC.yaml"
    if voc_yaml.exists():
        with open(voc_yaml, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            datasets.append({
                "name": "Pascal VOC",
                "path": str(voc_yaml),
                "type": "voc",
                "classes": config.get("names", []),
                "num_classes": config.get("nc", 0)
            })
    
    # 检查自定义数据集
    custom_dir = Path(settings.CUSTOM_DATASET_DIR)
    if custom_dir.exists():
        for yaml_file in custom_dir.glob("**/*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    datasets.append({
                        "name": yaml_file.stem,
                        "path": str(yaml_file),
                        "type": "custom",
                        "classes": config.get("names", []),
                        "num_classes": config.get("nc", 0)
                    })
            except:
                pass
    
    return {"datasets": datasets}


@router.get("/{dataset_name}")
async def get_dataset_info(dataset_name: str):
    """
    获取数据集详细信息
    """
    # 查找数据集配置文件
    yaml_path = None
    
    # 检查预定义数据集
    if dataset_name.lower() == "coco":
        yaml_path = DATASET_DIR / "coco" / "coco.yaml"
    elif dataset_name.lower() == "voc":
        yaml_path = YOLOV5_DIR / "data" / "VOC.yaml"
    else:
        # 检查自定义数据集
        custom_path = Path(settings.CUSTOM_DATASET_DIR) / f"{dataset_name}.yaml"
        if custom_path.exists():
            yaml_path = custom_path
    
    if not yaml_path or not yaml_path.exists():
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 统计图像数量
    train_count = val_count = test_count = 0
    
    train_path = config.get("train", "")
    val_path = config.get("val", "")
    test_path = config.get("test", "")
    
    # 尝试统计图像数量
    for path, count_name in [(train_path, "train"), (val_path, "val"), (test_path, "test")]:
        if path:
            full_path = Path(path)
            if not full_path.is_absolute():
                full_path = yaml_path.parent / path
            
            if full_path.exists():
                count = len(list(full_path.glob("*.jpg"))) + len(list(full_path.glob("*.png")))
                if count_name == "train":
                    train_count = count
                elif count_name == "val":
                    val_count = count
                else:
                    test_count = count
    
    return {
        "name": dataset_name,
        "path": str(yaml_path),
        "classes": config.get("names", []),
        "num_classes": config.get("nc", 0),
        "split": {
            "train": train_count,
            "val": val_count,
            "test": test_count
        },
        "config": config
    }


@router.post("/create")
async def create_custom_dataset(
    name: str = Form(..., description="数据集名称"),
    classes: str = Form(..., description="类别列表，逗号分隔"),
    description: Optional[str] = Form(None, description="数据集描述")
):
    """
    创建自定义数据集
    """
    # 创建数据集目录结构
    dataset_dir = Path(settings.CUSTOM_DATASET_DIR) / name
    
    if dataset_dir.exists():
        raise HTTPException(status_code=400, detail="数据集已存在")
    
    try:
        # 创建目录结构
        (dataset_dir / "images" / "train").mkdir(parents=True)
        (dataset_dir / "images" / "val").mkdir(parents=True)
        (dataset_dir / "images" / "test").mkdir(parents=True)
        (dataset_dir / "labels" / "train").mkdir(parents=True)
        (dataset_dir / "labels" / "val").mkdir(parents=True)
        (dataset_dir / "labels" / "test").mkdir(parents=True)
        
        # 解析类别
        class_list = [c.strip() for c in classes.split(",")]
        
        # 创建配置文件
        config = {
            "path": str(dataset_dir),
            "train": "images/train",
            "val": "images/val",
            "test": "images/test",
            "nc": len(class_list),
            "names": class_list
        }
        
        if description:
            config["description"] = description
        
        yaml_path = dataset_dir / f"{name}.yaml"
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        return {
            "success": True,
            "message": "数据集创建成功",
            "dataset": {
                "name": name,
                "path": str(dataset_dir),
                "yaml_path": str(yaml_path),
                "classes": class_list
            }
        }
        
    except Exception as e:
        # 清理
        if dataset_dir.exists():
            shutil.rmtree(dataset_dir)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{dataset_name}/upload")
async def upload_dataset_images(
    dataset_name: str,
    files: List[UploadFile] = File(..., description="图像文件"),
    split: str = Form("train", description="数据集划分 (train/val/test)")
):
    """
    上传图像到数据集
    """
    if split not in ["train", "val", "test"]:
        raise HTTPException(status_code=400, detail="无效的数据集划分")
    
    # 查找数据集目录
    dataset_dir = Path(settings.CUSTOM_DATASET_DIR) / dataset_name
    
    if not dataset_dir.exists():
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    images_dir = dataset_dir / "images" / split
    images_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded = []
    failed = []
    
    for file in files:
        try:
            if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
                failed.append({"filename": file.filename, "error": "不支持的文件类型"})
                continue
            
            save_path = images_dir / file.filename
            content = await file.read()
            
            with open(save_path, "wb") as f:
                f.write(content)
            
            uploaded.append(file.filename)
            
        except Exception as e:
            failed.append({"filename": file.filename, "error": str(e)})
    
    return {
        "success": True,
        "uploaded": len(uploaded),
        "failed": len(failed),
        "uploaded_files": uploaded,
        "failed_files": failed
    }


@router.delete("/{dataset_name}")
async def delete_dataset(dataset_name: str):
    """
    删除自定义数据集
    """
    dataset_dir = Path(settings.CUSTOM_DATASET_DIR) / dataset_name
    
    if not dataset_dir.exists():
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    try:
        shutil.rmtree(dataset_dir)
        return {"success": True, "message": "数据集已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_name}/images")
async def list_dataset_images(
    dataset_name: str,
    split: str = "train",
    page: int = 1,
    page_size: int = 20
):
    """
    列出数据集中的图像
    """
    # 查找数据集目录
    dataset_dir = Path(settings.CUSTOM_DATASET_DIR) / dataset_name
    
    if not dataset_dir.exists():
        # 检查预定义数据集
        if dataset_name.lower() == "coco":
            dataset_dir = DATASET_DIR / "coco"
        elif dataset_name.lower() == "voc":
            dataset_dir = DATASET_DIR / "VOC"
    
    if not dataset_dir.exists():
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    images_dir = dataset_dir / "images" / split
    if not images_dir.exists():
        return {"images": [], "total": 0}
    
    # 获取图像列表
    images = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.bmp"]:
        images.extend(images_dir.glob(ext))
    
    # 排序
    images = sorted(images, key=lambda x: x.name)
    
    # 分页
    total = len(images)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = images[start:end]
    
    return {
        "images": [{"name": img.name, "path": str(img)} for img in paginated],
        "total": total,
        "page": page,
        "page_size": page_size
    }
