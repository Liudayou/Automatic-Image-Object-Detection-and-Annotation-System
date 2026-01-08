<template>
  <div class="batch-page">
    <div class="page-title">批量处理</div>
    
    <el-row :gutter="20">
      <!-- 左侧：上传和参数设置 -->
      <el-col :span="8">
        <div class="content-card">
          <h3 class="card-title">批量上传</h3>
          
          <el-upload
            ref="uploadRef"
            v-model:file-list="fileList"
            :auto-upload="false"
            :accept="'image/*'"
            multiple
            drag
            list-type="text"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽图像到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 JPG/PNG/BMP 格式，可多选
              </div>
            </template>
          </el-upload>
          
          <div class="file-count" v-if="fileList.length > 0">
            已选择 {{ fileList.length }} 个文件
          </div>
        </div>
        
        <div class="content-card">
          <h3 class="card-title">检测参数</h3>
          
          <el-form label-position="top" size="default">
            <el-form-item label="模型权重">
              <el-select v-model="detectParams.weights" style="width: 100%">
                <el-option 
                  v-for="w in availableWeights" 
                  :key="w" 
                  :label="w" 
                  :value="w" 
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="置信度阈值">
              <el-slider 
                v-model="detectParams.confThreshold" 
                :min="0" 
                :max="1" 
                :step="0.05"
                show-input
                :show-input-controls="false"
              />
            </el-form-item>
            
            <el-form-item label="IOU阈值">
              <el-slider 
                v-model="detectParams.iouThreshold" 
                :min="0" 
                :max="1" 
                :step="0.05"
                show-input
                :show-input-controls="false"
              />
            </el-form-item>
            
            <el-form-item label="推理尺寸">
              <el-select v-model="detectParams.imgSize" style="width: 100%">
                <el-option :value="320" label="320" />
                <el-option :value="416" label="416" />
                <el-option :value="640" label="640" />
                <el-option :value="1280" label="1280" />
              </el-select>
            </el-form-item>
          </el-form>
          
          <el-button 
            type="primary" 
            :loading="processing" 
            :disabled="fileList.length === 0"
            @click="startBatchDetection"
            style="width: 100%"
            size="large"
          >
            <el-icon><VideoPlay /></el-icon>
            {{ processing ? `处理中 (${processedCount}/${fileList.length})` : '开始批量检测' }}
          </el-button>
        </div>
      </el-col>
      
      <!-- 右侧：结果展示 -->
      <el-col :span="16">
        <div class="content-card results-container">
          <div class="results-header">
            <h3 class="card-title">
              检测结果
              <el-tag v-if="results.length > 0" size="small" type="success">
                {{ results.length }} 个
              </el-tag>
            </h3>
            
            <el-space v-if="results.length > 0">
              <el-button @click="exportAllResults" :loading="exporting">
                <el-icon><Download /></el-icon> 导出全部
              </el-button>
              <el-button @click="clearResults" type="danger" plain>
                <el-icon><Delete /></el-icon> 清空
              </el-button>
            </el-space>
          </div>
          
          <div v-if="results.length === 0" class="empty-state">
            <el-icon class="empty-icon"><PictureFilled /></el-icon>
            <p class="empty-text">暂无检测结果</p>
            <p style="color: #909399; font-size: 12px;">上传图像并开始批量检测</p>
          </div>
          
          <div v-else class="results-grid">
            <div 
              v-for="(result, index) in results" 
              :key="index"
              class="result-item"
              @click="viewResult(result)"
            >
              <div class="result-image">
                <img :src="getImageUrl(result)" :alt="result.filename" />
                <div class="detection-count">
                  {{ result.detections?.length || 0 }} 个目标
                </div>
              </div>
              <div class="result-info">
                <div class="filename" :title="result.filename">{{ result.filename }}</div>
                <div class="meta">
                  <span>{{ result.inference_time }}ms</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 统计信息 -->
        <div class="content-card" v-if="results.length > 0">
          <h3 class="card-title">统计信息</h3>
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="mini-stat">
                <div class="mini-stat-value">{{ results.length }}</div>
                <div class="mini-stat-label">处理图像</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="mini-stat">
                <div class="mini-stat-value">{{ totalDetections }}</div>
                <div class="mini-stat-label">检测目标</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="mini-stat">
                <div class="mini-stat-value">{{ averageTime }}ms</div>
                <div class="mini-stat-label">平均耗时</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="mini-stat">
                <div class="mini-stat-value">{{ totalTime }}ms</div>
                <div class="mini-stat-label">总耗时</div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-col>
    </el-row>
    
    <!-- 结果详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="检测详情" width="800px">
      <div v-if="selectedResult" class="detail-content">
        <div class="detail-image">
          <img :src="getImageUrl(selectedResult)" :alt="selectedResult.filename" />
        </div>
        <div class="detail-info">
          <h4>检测结果</h4>
          <el-table :data="selectedResult.detections" size="small" max-height="300">
            <el-table-column prop="class_name" label="类别" />
            <el-table-column label="置信度" width="100">
              <template #default="{ row }">
                {{ (row.confidence * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column label="位置" width="200">
              <template #default="{ row }">
                ({{ Math.round(row.bbox.x) }}, {{ Math.round(row.bbox.y) }})
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="goToAnnotation(selectedResult)">
          编辑标注
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 导出对话框 -->
    <el-dialog v-model="showExportDialog" title="导出设置" width="400px">
      <el-form label-position="top">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportFormat">
            <el-radio-button value="yolo">YOLO</el-radio-button>
            <el-radio-button value="coco">COCO</el-radio-button>
            <el-radio-button value="voc">VOC</el-radio-button>
            <el-radio-button value="json">JSON</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="includeImages">包含图像文件</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="doExport" :loading="exporting">导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()

const uploadRef = ref(null)
const fileList = ref([])
const processing = ref(false)
const processedCount = ref(0)
const exporting = ref(false)

const results = ref([])
const selectedResult = ref(null)
const showDetailDialog = ref(false)
const showExportDialog = ref(false)

const exportFormat = ref('yolo')
const includeImages = ref(false)

const availableWeights = ref([])

const detectParams = reactive({
  weights: 'yolov5s.pt',
  confThreshold: 0.25,
  iouThreshold: 0.45,
  imgSize: 640
})

// 计算属性
const totalDetections = computed(() => {
  return results.value.reduce((sum, r) => sum + (r.detections?.length || 0), 0)
})

const averageTime = computed(() => {
  if (results.value.length === 0) return 0
  const total = results.value.reduce((sum, r) => sum + (r.inference_time || 0), 0)
  return Math.round(total / results.value.length)
})

const totalTime = computed(() => {
  return results.value.reduce((sum, r) => sum + (r.inference_time || 0), 0)
})

onMounted(async () => {
  try {
    const res = await api.getWeights()
    availableWeights.value = res.data.weights
    if (availableWeights.value.length > 0) {
      detectParams.weights = availableWeights.value[0]
    }
  } catch (error) {
    console.error('获取模型列表失败:', error)
  }
})

const getImageUrl = (result) => {
  if (result.image_path) {
    return result.image_path
  }
  // 如果有本地文件，创建 URL
  if (result.file) {
    return URL.createObjectURL(result.file)
  }
  return ''
}

const startBatchDetection = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先上传图像')
    return
  }
  
  processing.value = true
  processedCount.value = 0
  results.value = []
  
  try {
    for (const fileItem of fileList.value) {
      const formData = new FormData()
      formData.append('file', fileItem.raw)
      formData.append('conf_threshold', detectParams.confThreshold)
      formData.append('iou_threshold', detectParams.iouThreshold)
      formData.append('img_size', detectParams.imgSize)
      formData.append('weights', detectParams.weights)
      
      try {
        const res = await api.detect(formData)
        results.value.push({
          ...res.data,
          filename: fileItem.name,
          file: fileItem.raw
        })
      } catch (error) {
        results.value.push({
          filename: fileItem.name,
          error: error.message,
          detections: []
        })
      }
      
      processedCount.value++
    }
    
    ElMessage.success(`批量检测完成，共处理 ${results.value.length} 张图像`)
    
  } catch (error) {
    ElMessage.error('批量检测失败: ' + error.message)
  } finally {
    processing.value = false
  }
}

const viewResult = (result) => {
  selectedResult.value = result
  showDetailDialog.value = true
}

const goToAnnotation = (result) => {
  // 保存结果到本地存储，然后跳转
  if (result.image_id) {
    router.push({
      path: '/detection',
      query: { imageId: result.image_id }
    })
  }
  showDetailDialog.value = false
}

const exportAllResults = () => {
  showExportDialog.value = true
}

const doExport = async () => {
  const imageIds = results.value
    .filter(r => r.image_id)
    .map(r => r.image_id)
  
  if (imageIds.length === 0) {
    ElMessage.warning('没有可导出的检测结果')
    return
  }
  
  exporting.value = true
  
  try {
    // 先保存所有标注
    for (const result of results.value) {
      if (result.image_id && result.detections) {
        await api.saveAnnotations({
          image_id: result.image_id,
          image_path: result.image_path,
          image_width: result.image_width,
          image_height: result.image_height,
          annotations: result.detections.map(d => ({
            id: d.id,
            class_id: d.class_id,
            class_name: d.class_name,
            bbox: d.bbox,
            is_manual: false,
            confidence: d.confidence
          }))
        })
      }
    }
    
    // 导出
    const res = await api.exportAnnotations({
      image_ids: imageIds,
      format: exportFormat.value,
      include_images: includeImages.value
    })
    
    ElMessage.success('导出成功')
    showExportDialog.value = false
    
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  } finally {
    exporting.value = false
  }
}

const clearResults = () => {
  results.value = []
  fileList.value = []
}
</script>

<style lang="scss" scoped>
.batch-page {
  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .file-count {
    margin-top: 10px;
    color: #409EFF;
    font-size: 14px;
  }
  
  .results-container {
    min-height: 400px;
  }
  
  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    
    .card-title {
      margin-bottom: 0;
    }
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    
    .empty-icon {
      font-size: 60px;
      color: #dcdfe6;
      margin-bottom: 15px;
    }
    
    .empty-text {
      color: #909399;
      font-size: 16px;
    }
  }
  
  .results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 15px;
    max-height: 500px;
    overflow-y: auto;
  }
  
  .result-item {
    border: 1px solid #ebeef5;
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      border-color: #409EFF;
      box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
    }
    
    .result-image {
      position: relative;
      height: 120px;
      background: #f5f5f5;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      .detection-count {
        position: absolute;
        bottom: 5px;
        right: 5px;
        background: rgba(0, 0, 0, 0.7);
        color: #fff;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 12px;
      }
    }
    
    .result-info {
      padding: 10px;
      
      .filename {
        font-size: 14px;
        color: #303133;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      
      .meta {
        font-size: 12px;
        color: #909399;
        margin-top: 5px;
      }
    }
  }
  
  .mini-stat {
    text-align: center;
    padding: 15px;
    
    .mini-stat-value {
      font-size: 24px;
      font-weight: bold;
      color: #409EFF;
    }
    
    .mini-stat-label {
      font-size: 12px;
      color: #909399;
      margin-top: 5px;
    }
  }
  
  .detail-content {
    display: flex;
    gap: 20px;
    
    .detail-image {
      flex: 1;
      
      img {
        width: 100%;
        max-height: 400px;
        object-fit: contain;
        border-radius: 4px;
      }
    }
    
    .detail-info {
      flex: 1;
      
      h4 {
        margin-bottom: 10px;
        color: #303133;
      }
    }
  }
}
</style>
