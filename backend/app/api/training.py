"""
模型训练 API
"""
import os
import sys
import uuid
import json
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.config import settings, YOLOV5_DIR
from app.models import TrainingConfig, TrainingStatus, EvaluationResult

router = APIRouter()

# 训练任务状态存储
training_tasks: Dict[str, Dict[str, Any]] = {}


def run_training(task_id: str, config: TrainingConfig):
    """后台运行训练任务"""
    global training_tasks
    
    try:
        training_tasks[task_id]["status"] = "running"
        training_tasks[task_id]["message"] = "训练进行中..."
        
        # 构建训练命令
        train_script = YOLOV5_DIR / "train.py"
        
        # 确定权重路径
        weights_path = config.weights
        if not Path(weights_path).is_absolute():
            weights_path = str(YOLOV5_DIR / weights_path)
            if not Path(weights_path).exists():
                weights_path = str(YOLOV5_DIR / "weights" / config.weights)
        
        cmd = [
            sys.executable, str(train_script),
            "--weights", weights_path,
            "--data", config.data_yaml,
            "--epochs", str(config.epochs),
            "--batch-size", str(config.batch_size),
            "--img", str(config.img_size),
            "--project", config.project,
            "--name", config.name,
            "--workers", str(config.workers),
            "--patience", str(config.patience),
            "--optimizer", config.optimizer,
        ]
        
        if config.device:
            cmd.extend(["--device", config.device])
        
        # 执行训练
        process = subprocess.Popen(
            cmd,
            cwd=str(YOLOV5_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        training_tasks[task_id]["process"] = process
        
        # 读取输出并更新进度
        output_lines = []
        for line in process.stdout:
            output_lines.append(line.strip())
            training_tasks[task_id]["output"] = output_lines[-100:]  # 保留最后100行
            
            # 解析进度
            if "Epoch" in line:
                try:
                    # 解析类似 "Epoch 1/100" 的格式
                    parts = line.split("Epoch")[1].strip().split("/")
                    if len(parts) >= 2:
                        current = int(parts[0].split()[0])
                        total = int(parts[1].split()[0])
                        training_tasks[task_id]["current_epoch"] = current
                        training_tasks[task_id]["total_epochs"] = total
                        training_tasks[task_id]["progress"] = (current / total) * 100
                except:
                    pass
        
        process.wait()
        
        if process.returncode == 0:
            training_tasks[task_id]["status"] = "completed"
            training_tasks[task_id]["message"] = "训练完成"
            training_tasks[task_id]["progress"] = 100
            
            # 查找最新的训练结果
            results_dir = YOLOV5_DIR / config.project / config.name
            if results_dir.exists():
                training_tasks[task_id]["results_dir"] = str(results_dir)
        else:
            training_tasks[task_id]["status"] = "failed"
            training_tasks[task_id]["message"] = f"训练失败，返回码: {process.returncode}"
            
    except Exception as e:
        training_tasks[task_id]["status"] = "failed"
        training_tasks[task_id]["message"] = str(e)


@router.post("/start")
async def start_training(config: TrainingConfig, background_tasks: BackgroundTasks):
    """
    启动模型训练
    """
    # 验证数据集配置文件
    if not Path(config.data_yaml).exists():
        # 检查相对于 yolov5 目录
        data_yaml_path = YOLOV5_DIR / config.data_yaml
        if not data_yaml_path.exists():
            data_yaml_path = YOLOV5_DIR / "data" / config.data_yaml
            if not data_yaml_path.exists():
                raise HTTPException(
                    status_code=400, 
                    detail=f"数据集配置文件不存在: {config.data_yaml}"
                )
        config.data_yaml = str(data_yaml_path)
    
    # 创建训练任务
    task_id = str(uuid.uuid4())
    training_tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "current_epoch": 0,
        "total_epochs": config.epochs,
        "config": config.dict(),
        "created_at": datetime.now().isoformat(),
        "message": "准备开始训练...",
        "output": []
    }
    
    # 后台启动训练
    thread = threading.Thread(target=run_training, args=(task_id, config))
    thread.start()
    
    return {
        "task_id": task_id,
        "message": "训练任务已创建",
        "status": "pending"
    }


@router.get("/status/{task_id}")
async def get_training_status(task_id: str):
    """
    获取训练状态
    """
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    task = training_tasks[task_id]
    return TrainingStatus(
        task_id=task["task_id"],
        status=task["status"],
        progress=task.get("progress", 0),
        current_epoch=task.get("current_epoch", 0),
        total_epochs=task.get("total_epochs", 0),
        message=task.get("message"),
        metrics=task.get("metrics")
    )


@router.get("/output/{task_id}")
async def get_training_output(task_id: str):
    """
    获取训练输出日志
    """
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    return {
        "task_id": task_id,
        "output": training_tasks[task_id].get("output", [])
    }


@router.post("/stop/{task_id}")
async def stop_training(task_id: str):
    """
    停止训练任务
    """
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    task = training_tasks[task_id]
    
    if task.get("process"):
        task["process"].terminate()
        task["status"] = "stopped"
        task["message"] = "训练已手动停止"
        return {"success": True, "message": "训练已停止"}
    
    return {"success": False, "message": "无法停止训练"}


@router.get("/list")
async def list_training_tasks():
    """
    列出所有训练任务
    """
    tasks = []
    for task_id, task in training_tasks.items():
        tasks.append({
            "task_id": task_id,
            "status": task["status"],
            "progress": task.get("progress", 0),
            "created_at": task.get("created_at"),
            "message": task.get("message")
        })
    
    return {"tasks": tasks, "total": len(tasks)}


@router.get("/results/{task_id}")
async def get_training_results(task_id: str):
    """
    获取训练结果
    """
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    task = training_tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="训练尚未完成")
    
    results_dir = task.get("results_dir")
    if not results_dir or not Path(results_dir).exists():
        raise HTTPException(status_code=404, detail="训练结果目录不存在")
    
    results_path = Path(results_dir)
    
    # 读取训练结果
    result = {
        "task_id": task_id,
        "results_dir": results_dir,
        "weights": {}
    }
    
    # 检查权重文件
    for weight_file in ["best.pt", "last.pt"]:
        weight_path = results_path / "weights" / weight_file
        if weight_path.exists():
            result["weights"][weight_file] = str(weight_path)
    
    # 检查结果图表
    result["plots"] = []
    for plot_file in results_path.glob("*.png"):
        result["plots"].append(str(plot_file))
    
    # 读取 results.csv
    results_csv = results_path / "results.csv"
    if results_csv.exists():
        import pandas as pd
        df = pd.read_csv(results_csv)
        result["metrics_history"] = df.to_dict(orient="records")
    
    return result


@router.get("/datasets")
async def list_available_datasets():
    """
    列出可用的数据集配置
    """
    datasets = []
    
    # 检查 yolov5/data 目录
    data_dir = YOLOV5_DIR / "data"
    if data_dir.exists():
        for yaml_file in data_dir.glob("*.yaml"):
            datasets.append({
                "name": yaml_file.stem,
                "path": str(yaml_file),
                "relative_path": f"data/{yaml_file.name}"
            })
    
    # 检查自定义数据集目录
    custom_dir = Path(settings.CUSTOM_DATASET_DIR)
    if custom_dir.exists():
        for yaml_file in custom_dir.glob("**/*.yaml"):
            datasets.append({
                "name": yaml_file.stem,
                "path": str(yaml_file),
                "relative_path": str(yaml_file.relative_to(custom_dir.parent))
            })
    
    return {"datasets": datasets}


@router.get("/hyperparameters")
async def list_hyperparameters():
    """
    列出可用的超参数配置
    """
    hyps = []
    
    hyps_dir = YOLOV5_DIR / "data" / "hyps"
    if hyps_dir.exists():
        for yaml_file in hyps_dir.glob("*.yaml"):
            hyps.append({
                "name": yaml_file.stem,
                "path": str(yaml_file)
            })
    
    return {"hyperparameters": hyps}
