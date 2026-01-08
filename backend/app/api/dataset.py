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
    voc_yaml = DATASET_DIR / "VOC" / "VOC.yaml"
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
    dataset_base_dir = None
    
    # 检查预定义数据集
    dataset_name_lower = dataset_name.lower().replace(" ", "")
    if dataset_name_lower == "coco":
        yaml_path = DATASET_DIR / "coco" / "coco.yaml"
        dataset_base_dir = DATASET_DIR / "coco"
    elif dataset_name_lower in ["voc", "pascalvoc"]:
        yaml_path = DATASET_DIR / "VOC" / "VOC.yaml"
        dataset_base_dir = DATASET_DIR / "VOC"
    else:
        # 检查自定义数据集
        custom_path = Path(settings.CUSTOM_DATASET_DIR) / f"{dataset_name}.yaml"
        if custom_path.exists():
            yaml_path = custom_path
            dataset_base_dir = custom_path.parent
    
    if not yaml_path or not yaml_path.exists():
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 统计图像数量
    train_count = val_count = test_count = 0
    
    train_paths = config.get("train", "")
    val_paths = config.get("val", "")
    test_paths = config.get("test", "")
    
    # 辅助函数：统计目录中的图像数量
    def count_images_in_paths(paths, base_dir):
        """统计路径（可以是单个路径或路径列表）中的图像数量"""
        if not paths:
            return 0
        
        # 确保是列表
        if isinstance(paths, str):
            paths = [paths]
        
        total = 0
        for path in paths:
            full_path = Path(path)
            if not full_path.is_absolute():
                full_path = base_dir / path
            
            if full_path.exists() and full_path.is_dir():
                total += len(list(full_path.glob("*.jpg")))
                total += len(list(full_path.glob("*.jpeg")))
                total += len(list(full_path.glob("*.png")))
        
        return total
    
    train_count = count_images_in_paths(train_paths, dataset_base_dir)
    val_count = count_images_in_paths(val_paths, dataset_base_dir)
    test_count = count_images_in_paths(test_paths, dataset_base_dir)
    
    return {
        "name": dataset_name,
        "path": str(yaml_path),
        "classes": config.get("names", []),
        "num_classes": config.get("nc", len(config.get("names", [])) if isinstance(config.get("names"), (list, dict)) else 0),
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
    is_voc = False
    is_coco = False
    
    if not dataset_dir.exists():
        # 检查预定义数据集
        dataset_name_lower = dataset_name.lower().replace(" ", "")
        if dataset_name_lower == "coco":
            dataset_dir = DATASET_DIR / "coco"
            is_coco = True
        elif dataset_name_lower in ["voc", "pascalvoc"]:
            dataset_dir = DATASET_DIR / "VOC"
            is_voc = True
    
    if not dataset_dir.exists():
        raise HTTPException(status_code=404, detail=f"数据集目录不存在: {dataset_dir}")
    
    # 查找图像目录
    images = []
    images_dir = dataset_dir / "images"
    
    if not images_dir.exists():
        raise HTTPException(status_code=404, detail=f"图像目录不存在: {images_dir}")
    
    if is_voc:
        # VOC 数据集特殊处理: train2007, train2012, val2007, val2012 等
        # 根据 split 匹配对应目录（train 匹配 train2007, train2012; val 匹配 val2007, val2012; test 匹配 test2007）
        for subdir in images_dir.iterdir():
            if subdir.is_dir() and subdir.name.startswith(split):
                for ext in ["*.jpg", "*.jpeg", "*.png", "*.bmp"]:
                    images.extend(subdir.glob(ext))
    elif is_coco:
        # COCO 数据集: train2017, val2017, test2017
        split_dir = images_dir / f"{split}2017"
        if split_dir.exists():
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.bmp"]:
                images.extend(split_dir.glob(ext))
    else:
        # 自定义数据集
        split_dir = images_dir / split
        if split_dir.exists():
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.bmp"]:
                images.extend(split_dir.glob(ext))
        elif images_dir.exists():
            # 直接在 images 目录下查找
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.bmp"]:
                images.extend(images_dir.glob(ext))
    
    # 排序
    images = sorted(images, key=lambda x: x.name)
    
    # 分页
    total = len(images)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = images[start:end]
    
    # 转换路径为URL
    def get_image_url(img_path: Path) -> str:
        # 获取相对于数据集目录的路径
        try:
            rel_path = img_path.relative_to(DATASET_DIR)
            return f"/datasets/{rel_path.as_posix()}"
        except ValueError:
            # 自定义数据集
            try:
                rel_path = img_path.relative_to(Path(settings.CUSTOM_DATASET_DIR))
                return f"/custom_datasets/{rel_path.as_posix()}"
            except ValueError:
                return str(img_path)
    
    return {
        "images": [{"name": img.name, "path": get_image_url(img)} for img in paginated],
        "total": total,
        "page": page,
        "page_size": page_size
    }
