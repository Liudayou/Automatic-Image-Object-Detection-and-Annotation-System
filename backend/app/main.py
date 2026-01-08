"""
FastAPI 主应用入口
"""
import sys
from pathlib import Path

# 添加 yolov5 到系统路径
YOLOV5_PATH = Path(__file__).resolve().parent.parent.parent / "yolov5"
if str(YOLOV5_PATH) not in sys.path:
    sys.path.insert(0, str(YOLOV5_PATH))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api import detection, annotation, training, dataset, export, preprocessing

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于YOLOv5的自动图像目标检测与标注系统API",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/exports", StaticFiles(directory=settings.EXPORT_DIR), name="exports")

# 数据集静态文件服务
from app.config import DATASET_DIR
app.mount("/datasets", StaticFiles(directory=str(DATASET_DIR)), name="datasets")

# 自定义数据集静态文件服务
import os
custom_datasets_dir = settings.CUSTOM_DATASET_DIR
if os.path.exists(custom_datasets_dir):
    app.mount("/custom_datasets", StaticFiles(directory=custom_datasets_dir), name="custom_datasets")

# 注册路由
app.include_router(detection.router, prefix="/api/detection", tags=["目标检测"])
app.include_router(annotation.router, prefix="/api/annotation", tags=["标注管理"])
app.include_router(training.router, prefix="/api/training", tags=["模型训练"])
app.include_router(dataset.router, prefix="/api/dataset", tags=["数据集管理"])
app.include_router(export.router, prefix="/api/export", tags=["导出功能"])
app.include_router(preprocessing.router, prefix="/api/preprocessing", tags=["数据预处理"])

@app.get("/", tags=["系统"])
async def root():
    """系统根路径"""
    return {
        "message": f"欢迎使用{settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }

@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": settings.APP_VERSION}

@app.get("/api/system/info", tags=["系统"])
async def system_info():
    """获取系统信息"""
    import torch
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
