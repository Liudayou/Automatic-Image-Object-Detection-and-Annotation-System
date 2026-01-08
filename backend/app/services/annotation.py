"""
标注服务
"""
import json
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

from app.config import settings
from app.models import Annotation, AnnotationSaveRequest, ExportFormat, BoundingBox


class AnnotationService:
    """标注数据管理服务"""
    
    def __init__(self):
        self.annotations_dir = Path(settings.UPLOAD_DIR) / "annotations"
        self.annotations_dir.mkdir(parents=True, exist_ok=True)
    
    def save_annotations(self, request: AnnotationSaveRequest) -> Dict[str, Any]:
        """保存标注数据"""
        annotation_file = self.annotations_dir / f"{request.image_id}.json"
        
        data = {
            "image_id": request.image_id,
            "image_path": request.image_path,
            "image_width": request.image_width,
            "image_height": request.image_height,
            "annotations": [ann.model_dump() for ann in request.annotations],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        with open(annotation_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "image_id": request.image_id,
            "annotation_count": len(request.annotations),
            "file_path": str(annotation_file)
        }
    
    def get_annotations(self, image_id: str) -> Optional[Dict[str, Any]]:
        """获取标注数据"""
        annotation_file = self.annotations_dir / f"{image_id}.json"
        
        if not annotation_file.exists():
            return None
        
        with open(annotation_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def delete_annotations(self, image_id: str) -> bool:
        """删除标注数据"""
        annotation_file = self.annotations_dir / f"{image_id}.json"
        
        if annotation_file.exists():
            annotation_file.unlink()
            return True
        return False
    
    def list_annotations(self) -> List[Dict[str, Any]]:
        """列出所有标注"""
        annotations = []
        for file in self.annotations_dir.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                annotations.append({
                    "image_id": data["image_id"],
                    "image_path": data["image_path"],
                    "annotation_count": len(data["annotations"]),
                    "updated_at": data.get("updated_at")
                })
        return annotations
    
    def export_annotations(
        self,
        image_ids: List[str],
        format: ExportFormat,
        output_dir: str = None
    ) -> Dict[str, Any]:
        """导出标注数据"""
        if output_dir is None:
            export_id = str(uuid.uuid4())[:8]
            output_dir = Path(settings.EXPORT_DIR) / f"export_{export_id}"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        
        for image_id in image_ids:
            annotation_data = self.get_annotations(image_id)
            if annotation_data is None:
                continue
            
            if format == ExportFormat.YOLO:
                file_path = self._export_yolo(annotation_data, output_dir)
            elif format == ExportFormat.COCO:
                file_path = self._export_coco(annotation_data, output_dir)
            elif format == ExportFormat.VOC:
                file_path = self._export_voc(annotation_data, output_dir)
            else:  # JSON
                file_path = self._export_json(annotation_data, output_dir)
            
            exported_files.append(file_path)
        
        return {
            "success": True,
            "format": format.value,
            "output_dir": str(output_dir),
            "exported_count": len(exported_files),
            "files": exported_files
        }
    
    def _export_yolo(self, data: Dict, output_dir: Path) -> str:
        """导出为 YOLO 格式"""
        # YOLO格式: class_id x_center y_center width height (归一化)
        image_id = data["image_id"]
        img_w = data["image_width"]
        img_h = data["image_height"]
        
        labels_dir = output_dir / "labels"
        labels_dir.mkdir(exist_ok=True)
        
        file_path = labels_dir / f"{image_id}.txt"
        
        lines = []
        for ann in data["annotations"]:
            bbox = ann["bbox"]
            # 转换为 YOLO 格式 (归一化的中心点坐标和宽高)
            x_center = (bbox["x"] + bbox["width"] / 2) / img_w
            y_center = (bbox["y"] + bbox["height"] / 2) / img_h
            w = bbox["width"] / img_w
            h = bbox["height"] / img_h
            
            lines.append(f"{ann['class_id']} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")
        
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
        
        return str(file_path)
    
    def _export_coco(self, data: Dict, output_dir: Path) -> str:
        """导出为 COCO 格式"""
        image_id = data["image_id"]
        
        coco_data = {
            "images": [{
                "id": 1,
                "file_name": Path(data["image_path"]).name,
                "width": data["image_width"],
                "height": data["image_height"]
            }],
            "annotations": [],
            "categories": []
        }
        
        categories_set = set()
        for idx, ann in enumerate(data["annotations"]):
            bbox = ann["bbox"]
            coco_data["annotations"].append({
                "id": idx + 1,
                "image_id": 1,
                "category_id": ann["class_id"],
                "bbox": [bbox["x"], bbox["y"], bbox["width"], bbox["height"]],
                "area": bbox["width"] * bbox["height"],
                "iscrowd": 0
            })
            categories_set.add((ann["class_id"], ann["class_name"]))
        
        coco_data["categories"] = [
            {"id": cid, "name": name}
            for cid, name in sorted(categories_set)
        ]
        
        file_path = output_dir / f"{image_id}_coco.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(coco_data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def _export_voc(self, data: Dict, output_dir: Path) -> str:
        """导出为 Pascal VOC XML 格式"""
        image_id = data["image_id"]
        image_path = Path(data["image_path"])
        
        annotations_dir = output_dir / "Annotations"
        annotations_dir.mkdir(exist_ok=True)
        
        # 创建 XML 结构
        root = ET.Element("annotation")
        
        ET.SubElement(root, "folder").text = str(image_path.parent.name)
        ET.SubElement(root, "filename").text = image_path.name
        
        source = ET.SubElement(root, "source")
        ET.SubElement(source, "database").text = "Custom"
        
        size = ET.SubElement(root, "size")
        ET.SubElement(size, "width").text = str(data["image_width"])
        ET.SubElement(size, "height").text = str(data["image_height"])
        ET.SubElement(size, "depth").text = "3"
        
        ET.SubElement(root, "segmented").text = "0"
        
        for ann in data["annotations"]:
            obj = ET.SubElement(root, "object")
            ET.SubElement(obj, "name").text = ann["class_name"]
            ET.SubElement(obj, "pose").text = "Unspecified"
            ET.SubElement(obj, "truncated").text = "0"
            ET.SubElement(obj, "difficult").text = "0"
            
            bbox = ann["bbox"]
            bndbox = ET.SubElement(obj, "bndbox")
            ET.SubElement(bndbox, "xmin").text = str(int(bbox["x"]))
            ET.SubElement(bndbox, "ymin").text = str(int(bbox["y"]))
            ET.SubElement(bndbox, "xmax").text = str(int(bbox["x"] + bbox["width"]))
            ET.SubElement(bndbox, "ymax").text = str(int(bbox["y"] + bbox["height"]))
        
        # 格式化 XML
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        file_path = annotations_dir / f"{image_id}.xml"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        
        return str(file_path)
    
    def _export_json(self, data: Dict, output_dir: Path) -> str:
        """导出为 JSON 格式"""
        image_id = data["image_id"]
        file_path = output_dir / f"{image_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)


# 全局标注服务实例
annotation_service = AnnotationService()
