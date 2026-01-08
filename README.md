# 自动图像目标检测与标注系统

基于 YOLOv5 的自动图像目标检测与标注系统，支持目标检测、手动标注、模型训练、数据管理和导出功能。

## 功能特点

- 🎯 **目标检测与标注一体化**：在同一页面完成自动检测和手动标注
- 🖼️ **批量处理**：支持批量图像检测
- 🔧 **数据预处理**：图像增强、质量检测
- 📊 **模型训练**：支持自定义数据集训练 YOLOv5 模型
- 📁 **数据集管理**：支持 COCO、VOC 及自定义数据集
- 📤 **多格式导出**：YOLO、COCO、Pascal VOC、JSON

## 技术栈

### 后端
- FastAPI
- YOLOv5
- PyTorch
- OpenCV
- Pillow

### 前端
- Vue 3
- Element Plus
- Vite
- ECharts

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- CUDA (可选，用于 GPU 加速)

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/lcyxkwy/Automatic-Image-Object-Detection-and-Annotation-System.git
cd Automatic-Image-Object-Detection-and-Annotation-System
```

2. **安装后端依赖**
```bash
cd backend
pip install -r requirements.txt
```

3. **下载 YOLOv5 权重文件**
```bash
# 将权重文件放到 yolov5/ 目录下
# 可从 https://github.com/ultralytics/yolov5/releases 下载
```

4. **安装前端依赖**
```bash
cd frontend
npm install
```

### 启动服务

1. **启动后端**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **启动前端**
```bash
cd frontend
npm run dev
```

3. **访问系统**
- 前端界面: http://localhost:3000
- API 文档: http://localhost:8000/docs

## 项目结构

```
├── backend/                # 后端服务
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── services/      # 业务服务
│   │   ├── config.py      # 配置文件
│   │   ├── main.py        # 应用入口
│   │   └── models.py      # 数据模型
│   └── requirements.txt
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── api/           # API 封装
│   │   ├── views/         # 页面组件
│   │   ├── router/        # 路由配置
│   │   └── styles/        # 样式文件
│   └── package.json
├── yolov5/                 # YOLOv5 模型
├── dataset/                # 数据集目录
├── uploads/                # 上传文件目录
└── exports/                # 导出文件目录
```

## 页面说明

| 页面 | 功能 |
|------|------|
| 首页 | 系统概览、快捷操作 |
| 检测与标注 | 图像检测、手动标注、标注编辑 |
| 批量处理 | 批量图像检测 |
| 模型训练 | 配置和监控模型训练 |
| 数据集管理 | 管理数据集、上传图像 |
| 数据预处理 | 图像增强、质量检测 |
| 导出管理 | 导出标注数据 |

## 许可证

MIT License
