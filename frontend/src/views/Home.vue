<template>
  <div class="home-page">
    <div class="page-title">系统概览</div>
    
    <!-- 欢迎信息 -->
    <div class="content-card welcome-card">
      <div class="welcome-content">
        <h2>欢迎使用自动图像目标检测与标注系统</h2>
        <p>基于 YOLOv5 深度学习算法，提供高效的目标检测与标注功能</p>
        <el-button type="primary" size="large" @click="$router.push('/detection')">
          <el-icon><Camera /></el-icon>
          开始检测
        </el-button>
      </div>
      <div class="welcome-image">
        <img src="@/assets/logo.svg" alt="logo" />
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <div class="content-card stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #409EFF, #66b1ff)">
            <el-icon><Picture /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.annotationCount }}</div>
            <div class="stat-label">已标注图像</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="content-card stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #67C23A, #85ce61)">
            <el-icon><Files /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.datasetCount }}</div>
            <div class="stat-label">数据集</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="content-card stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #E6A23C, #ebb563)">
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.modelCount }}</div>
            <div class="stat-label">可用模型</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="content-card stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #F56C6C, #f78989)">
            <el-icon><DataLine /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.trainingCount }}</div>
            <div class="stat-label">训练任务</div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 功能模块 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="content-card">
          <h3 class="card-title">快捷功能</h3>
          <div class="quick-actions">
            <div class="action-item" @click="$router.push('/detection')">
              <el-icon class="action-icon"><Camera /></el-icon>
              <span>目标检测与标注</span>
              <p>上传图像进行自动检测和手动标注</p>
            </div>
            <div class="action-item" @click="$router.push('/batch')">
              <el-icon class="action-icon"><Files /></el-icon>
              <span>批量处理</span>
              <p>批量上传图像进行检测处理</p>
            </div>
            <div class="action-item" @click="$router.push('/training')">
              <el-icon class="action-icon"><DataLine /></el-icon>
              <span>模型训练</span>
              <p>使用自定义数据集训练模型</p>
            </div>
            <div class="action-item" @click="$router.push('/dataset')">
              <el-icon class="action-icon"><FolderOpened /></el-icon>
              <span>数据集管理</span>
              <p>管理和创建训练数据集</p>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :span="12">
        <div class="content-card">
          <h3 class="card-title">系统信息</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统名称">{{ systemInfo.app_name || '自动图像目标检测与标注系统' }}</el-descriptions-item>
            <el-descriptions-item label="版本">{{ systemInfo.version || '1.0.0' }}</el-descriptions-item>
            <el-descriptions-item label="GPU 加速">
              <el-tag :type="systemInfo.cuda_available ? 'success' : 'info'">
                {{ systemInfo.cuda_available ? '已启用' : '未启用' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="GPU 设备" v-if="systemInfo.cuda_device_name">
              {{ systemInfo.cuda_device_name }}
            </el-descriptions-item>
            <el-descriptions-item label="检测模型">YOLOv5</el-descriptions-item>
            <el-descriptions-item label="支持类别">80 类 (COCO)</el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div class="content-card" style="margin-top: 20px;">
          <h3 class="card-title">可用模型</h3>
          <el-table :data="availableWeights" size="small" max-height="200">
            <el-table-column prop="name" label="模型名称" />
            <el-table-column prop="size" label="大小" width="100" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button type="primary" size="small" text @click="useModel(row)">
                  使用
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

const stats = ref({
  annotationCount: 0,
  datasetCount: 0,
  modelCount: 0,
  trainingCount: 0
})

const systemInfo = ref({})
const availableWeights = ref([])

onMounted(async () => {
  // 获取系统信息
  try {
    const res = await api.getSystemInfo()
    systemInfo.value = res.data
  } catch (error) {
    console.error('获取系统信息失败:', error)
  }
  
  // 获取可用模型
  try {
    const res = await api.getWeights()
    availableWeights.value = res.data.weights.map(w => ({
      name: w,
      size: getModelSize(w)
    }))
    stats.value.modelCount = availableWeights.value.length
  } catch (error) {
    console.error('获取模型列表失败:', error)
  }
  
  // 获取标注统计
  try {
    const res = await api.listAnnotations(1, 1)
    stats.value.annotationCount = res.data.total
  } catch (error) {
    console.error('获取标注统计失败:', error)
  }
  
  // 获取数据集统计
  try {
    const res = await api.listDatasets()
    stats.value.datasetCount = res.data.datasets.length
  } catch (error) {
    console.error('获取数据集统计失败:', error)
  }
  
  // 获取训练任务统计
  try {
    const res = await api.listTrainingTasks()
    stats.value.trainingCount = res.data.total
  } catch (error) {
    console.error('获取训练任务统计失败:', error)
  }
})

const getModelSize = (name) => {
  const sizes = {
    'yolov5n.pt': '3.9 MB',
    'yolov5s.pt': '14.1 MB',
    'yolov5m.pt': '40.8 MB',
    'yolov5l.pt': '89.3 MB',
    'yolov5x.pt': '166.0 MB'
  }
  return sizes[name] || '-'
}

const useModel = (model) => {
  router.push({
    path: '/detection',
    query: { weights: model.name }
  })
}
</script>

<style lang="scss" scoped>
.home-page {
  .welcome-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    
    .welcome-content {
      h2 {
        font-size: 24px;
        margin-bottom: 10px;
      }
      
      p {
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 20px;
      }
      
      .el-button {
        background: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.3);
        
        &:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      }
    }
    
    .welcome-image {
      img {
        width: 120px;
        height: 120px;
        opacity: 0.8;
      }
    }
  }
  
  .stat-row {
    margin-top: 20px;
    margin-bottom: 20px;
  }
  
  .stat-card {
    display: flex;
    align-items: center;
    gap: 15px;
    
    .stat-icon {
      width: 60px;
      height: 60px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .el-icon {
        font-size: 28px;
        color: #fff;
      }
    }
    
    .stat-info {
      .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: #303133;
      }
      
      .stat-label {
        font-size: 14px;
        color: #909399;
      }
    }
  }
  
  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 15px;
  }
  
  .quick-actions {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
    
    .action-item {
      padding: 20px;
      border: 1px solid #ebeef5;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s;
      
      &:hover {
        border-color: #409EFF;
        box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
        transform: translateY(-2px);
      }
      
      .action-icon {
        font-size: 32px;
        color: #409EFF;
        margin-bottom: 10px;
      }
      
      span {
        display: block;
        font-size: 16px;
        font-weight: 500;
        color: #303133;
        margin-bottom: 5px;
      }
      
      p {
        font-size: 12px;
        color: #909399;
        margin: 0;
      }
    }
  }
}
</style>
