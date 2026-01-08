<template>
  <div class="preprocessing-page">
    <div class="page-title">数据预处理</div>
    
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 图像增强 -->
      <el-tab-pane label="图像增强" name="augment">
        <el-row :gutter="20">
          <el-col :span="10">
            <div class="upload-section">
              <h4>上传图像</h4>
              <el-upload
                ref="augmentUploadRef"
                v-model:file-list="augmentFiles"
                :auto-upload="false"
                :limit="1"
                accept="image/*"
                drag
                :on-exceed="handleExceed"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">拖拽图像到此处或点击上传</div>
              </el-upload>
            </div>
            
            <div class="params-section">
              <h4>增强参数</h4>
              
              <el-form label-position="top" size="small">
                <el-row :gutter="15">
                  <el-col :span="12">
                    <el-form-item label="调整宽度">
                      <el-input-number 
                        v-model="augmentParams.resize_width" 
                        :min="0" 
                        placeholder="可选"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="调整高度">
                      <el-input-number 
                        v-model="augmentParams.resize_height" 
                        :min="0"
                        placeholder="可选"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-form-item label="旋转角度">
                  <el-slider 
                    v-model="augmentParams.rotate" 
                    :min="-180" 
                    :max="180"
                    show-input
                  />
                </el-form-item>
                
                <el-row :gutter="15">
                  <el-col :span="12">
                    <el-form-item>
                      <el-checkbox v-model="augmentParams.flip_horizontal">
                        水平翻转
                      </el-checkbox>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item>
                      <el-checkbox v-model="augmentParams.flip_vertical">
                        垂直翻转
                      </el-checkbox>
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-form-item label="亮度调整 (0.5-2.0)">
                  <el-slider 
                    v-model="augmentParams.brightness" 
                    :min="0.5" 
                    :max="2"
                    :step="0.1"
                    show-input
                  />
                </el-form-item>
                
                <el-form-item label="对比度调整 (0.5-2.0)">
                  <el-slider 
                    v-model="augmentParams.contrast" 
                    :min="0.5" 
                    :max="2"
                    :step="0.1"
                    show-input
                  />
                </el-form-item>
                
                <el-form-item label="饱和度调整 (0.5-2.0)">
                  <el-slider 
                    v-model="augmentParams.saturation" 
                    :min="0.5" 
                    :max="2"
                    :step="0.1"
                    show-input
                  />
                </el-form-item>
                
                <el-form-item label="色调偏移 (-180-180)">
                  <el-slider 
                    v-model="augmentParams.hue_shift" 
                    :min="-180" 
                    :max="180"
                    show-input
                  />
                </el-form-item>
              </el-form>
              
              <el-button 
                type="primary" 
                :loading="augmenting"
                :disabled="augmentFiles.length === 0"
                @click="applyAugmentation"
                style="width: 100%"
              >
                应用增强
              </el-button>
              
              <el-button 
                @click="resetAugmentParams"
                style="width: 100%; margin-top: 10px;"
              >
                重置参数
              </el-button>
            </div>
          </el-col>
          
          <el-col :span="14">
            <div class="preview-section">
              <h4>预览对比</h4>
              <div class="preview-compare">
                <div class="preview-item">
                  <div class="preview-label">原始图像</div>
                  <div class="preview-image">
                    <img 
                      v-if="originalPreview" 
                      :src="originalPreview" 
                      alt="原始图像"
                    />
                    <el-empty v-else description="请上传图像" :image-size="60" />
                  </div>
                </div>
                <div class="preview-arrow">
                  <el-icon><Right /></el-icon>
                </div>
                <div class="preview-item">
                  <div class="preview-label">增强结果</div>
                  <div class="preview-image">
                    <img 
                      v-if="augmentedPreview" 
                      :src="augmentedPreview" 
                      alt="增强结果"
                    />
                    <el-empty v-else description="等待增强" :image-size="60" />
                  </div>
                </div>
              </div>
              
              <div v-if="augmentResult" class="result-info">
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="原始尺寸">
                    {{ augmentResult.original_size?.width }} × {{ augmentResult.original_size?.height }}
                  </el-descriptions-item>
                  <el-descriptions-item label="增强后尺寸">
                    {{ augmentResult.augmented_size?.width }} × {{ augmentResult.augmented_size?.height }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-tab-pane>
      
      <!-- 质量检测 -->
      <el-tab-pane label="质量检测" name="quality">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="upload-section">
              <h4>上传图像</h4>
              <el-upload
                ref="qualityUploadRef"
                v-model:file-list="qualityFiles"
                :auto-upload="false"
                accept="image/*"
                multiple
                drag
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">拖拽图像到此处或点击上传</div>
                <template #tip>
                  <div class="el-upload__tip">支持批量上传检测</div>
                </template>
              </el-upload>
            </div>
            
            <div class="params-section">
              <h4>检测参数</h4>
              <el-form label-position="top">
                <el-form-item label="模糊度阈值">
                  <el-slider 
                    v-model="qualityParams.blur_threshold" 
                    :min="10" 
                    :max="500"
                    show-input
                  />
                  <div class="param-tip">分数低于此值将被判定为模糊</div>
                </el-form-item>
              </el-form>
              
              <el-button 
                type="primary" 
                :loading="checking"
                :disabled="qualityFiles.length === 0"
                @click="checkQuality"
                style="width: 100%"
              >
                开始检测 ({{ qualityFiles.length }} 张)
              </el-button>
            </div>
          </el-col>
          
          <el-col :span="16">
            <div class="quality-results">
              <div class="results-header">
                <h4>检测结果</h4>
                <div v-if="qualityResults.length > 0" class="quality-stats">
                  <el-tag type="success">
                    合格: {{ qualityResults.filter(r => !r.is_blurry).length }}
                  </el-tag>
                  <el-tag type="danger">
                    模糊: {{ qualityResults.filter(r => r.is_blurry).length }}
                  </el-tag>
                  <el-tag type="info">
                    质量率: {{ qualityRate }}%
                  </el-tag>
                </div>
              </div>
              
              <el-table 
                :data="qualityResults" 
                v-loading="checking"
                max-height="400"
              >
                <el-table-column prop="filename" label="文件名" />
                <el-table-column prop="blur_score" label="清晰度分数" width="120">
                  <template #default="{ row }">
                    {{ row.blur_score?.toFixed(2) }}
                  </template>
                </el-table-column>
                <el-table-column prop="quality" label="质量" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.is_blurry ? 'danger' : 'success'" size="small">
                      {{ row.quality }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="80">
                  <template #default="{ row }">
                    <el-icon v-if="row.is_blurry" color="#F56C6C"><CircleClose /></el-icon>
                    <el-icon v-else color="#67C23A"><CircleCheck /></el-icon>
                  </template>
                </el-table-column>
              </el-table>
              
              <el-empty v-if="qualityResults.length === 0 && !checking" description="请上传图像进行质量检测" />
            </div>
          </el-col>
        </el-row>
      </el-tab-pane>
      
      <!-- 批量增强 -->
      <el-tab-pane label="批量增强" name="batch">
        <el-row :gutter="20">
          <el-col :span="10">
            <div class="upload-section">
              <h4>批量上传</h4>
              <el-upload
                v-model:file-list="batchFiles"
                :auto-upload="false"
                accept="image/*"
                multiple
                drag
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">拖拽图像到此处或点击上传</div>
              </el-upload>
              <div class="file-count">已选择 {{ batchFiles.length }} 个文件</div>
            </div>
            
            <div class="params-section">
              <h4>批量增强配置</h4>
              <el-form label-position="top" size="small">
                <el-form-item label="统一调整尺寸">
                  <el-row :gutter="10">
                    <el-col :span="12">
                      <el-input-number 
                        v-model="batchParams.resize[0]" 
                        :min="0"
                        placeholder="宽度"
                        style="width: 100%"
                      />
                    </el-col>
                    <el-col :span="12">
                      <el-input-number 
                        v-model="batchParams.resize[1]" 
                        :min="0"
                        placeholder="高度"
                        style="width: 100%"
                      />
                    </el-col>
                  </el-row>
                </el-form-item>
                
                <el-form-item>
                  <el-checkbox v-model="batchParams.flip_horizontal">
                    水平翻转
                  </el-checkbox>
                </el-form-item>
                
                <el-form-item label="亮度调整">
                  <el-slider 
                    v-model="batchParams.brightness" 
                    :min="0.5" 
                    :max="2"
                    :step="0.1"
                    show-input
                  />
                </el-form-item>
                
                <el-form-item label="对比度调整">
                  <el-slider 
                    v-model="batchParams.contrast" 
                    :min="0.5" 
                    :max="2"
                    :step="0.1"
                    show-input
                  />
                </el-form-item>
              </el-form>
              
              <el-button 
                type="primary" 
                :loading="batchProcessing"
                :disabled="batchFiles.length === 0"
                @click="batchAugment"
                style="width: 100%"
              >
                开始批量增强
              </el-button>
            </div>
          </el-col>
          
          <el-col :span="14">
            <div class="batch-results">
              <h4>处理结果</h4>
              
              <el-progress 
                v-if="batchProcessing"
                :percentage="batchProgress"
                :status="batchProgress === 100 ? 'success' : ''"
              />
              
              <el-table :data="batchResults" max-height="400">
                <el-table-column prop="original_name" label="原文件名" />
                <el-table-column label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.success ? 'success' : 'danger'" size="small">
                      {{ row.success ? '成功' : '失败' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="error" label="错误信息" v-if="batchResults.some(r => r.error)" />
              </el-table>
              
              <el-empty v-if="batchResults.length === 0 && !batchProcessing" description="请上传图像进行批量增强" />
            </div>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const activeTab = ref('augment')

// 图像增强
const augmentUploadRef = ref(null)
const augmentFiles = ref([])
const augmenting = ref(false)
const originalPreview = ref(null)
const augmentedPreview = ref(null)
const augmentResult = ref(null)

const augmentParams = reactive({
  resize_width: null,
  resize_height: null,
  rotate: 0,
  flip_horizontal: false,
  flip_vertical: false,
  brightness: 1.0,
  contrast: 1.0,
  saturation: 1.0,
  hue_shift: 0
})

// 质量检测
const qualityUploadRef = ref(null)
const qualityFiles = ref([])
const checking = ref(false)
const qualityResults = ref([])

const qualityParams = reactive({
  blur_threshold: 100
})

// 批量增强
const batchFiles = ref([])
const batchProcessing = ref(false)
const batchProgress = ref(0)
const batchResults = ref([])

const batchParams = reactive({
  resize: [640, 640],
  flip_horizontal: false,
  brightness: 1.0,
  contrast: 1.0
})

// 计算属性
const qualityRate = computed(() => {
  if (qualityResults.value.length === 0) return 0
  const goodCount = qualityResults.value.filter(r => !r.is_blurry).length
  return Math.round((goodCount / qualityResults.value.length) * 100)
})

// 监听文件变化，更新预览
watch(augmentFiles, (files) => {
  if (files.length > 0) {
    const file = files[0].raw
    originalPreview.value = URL.createObjectURL(file)
    augmentedPreview.value = null
    augmentResult.value = null
  } else {
    originalPreview.value = null
    augmentedPreview.value = null
    augmentResult.value = null
  }
})

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件，请先删除已选文件')
}

const applyAugmentation = async () => {
  if (augmentFiles.value.length === 0) return
  
  augmenting.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', augmentFiles.value[0].raw)
    
    if (augmentParams.resize_width) {
      formData.append('resize_width', augmentParams.resize_width)
    }
    if (augmentParams.resize_height) {
      formData.append('resize_height', augmentParams.resize_height)
    }
    if (augmentParams.rotate !== 0) {
      formData.append('rotate', augmentParams.rotate)
    }
    formData.append('flip_horizontal', augmentParams.flip_horizontal)
    formData.append('flip_vertical', augmentParams.flip_vertical)
    if (augmentParams.brightness !== 1.0) {
      formData.append('brightness', augmentParams.brightness)
    }
    if (augmentParams.contrast !== 1.0) {
      formData.append('contrast', augmentParams.contrast)
    }
    if (augmentParams.saturation !== 1.0) {
      formData.append('saturation', augmentParams.saturation)
    }
    if (augmentParams.hue_shift !== 0) {
      formData.append('hue_shift', augmentParams.hue_shift)
    }
    
    const res = await api.augmentImage(formData)
    augmentResult.value = res.data
    augmentedPreview.value = res.data.augmented_path
    
    ElMessage.success('增强完成')
    
  } catch (error) {
    ElMessage.error('增强失败: ' + error.message)
  } finally {
    augmenting.value = false
  }
}

const resetAugmentParams = () => {
  augmentParams.resize_width = null
  augmentParams.resize_height = null
  augmentParams.rotate = 0
  augmentParams.flip_horizontal = false
  augmentParams.flip_vertical = false
  augmentParams.brightness = 1.0
  augmentParams.contrast = 1.0
  augmentParams.saturation = 1.0
  augmentParams.hue_shift = 0
}

const checkQuality = async () => {
  if (qualityFiles.value.length === 0) return
  
  checking.value = true
  qualityResults.value = []
  
  try {
    const formData = new FormData()
    qualityFiles.value.forEach(file => {
      formData.append('files', file.raw)
    })
    formData.append('blur_threshold', qualityParams.blur_threshold)
    
    const res = await api.batchQualityCheck(formData)
    qualityResults.value = res.data.results
    
    ElMessage.success(`检测完成，质量率: ${res.data.quality_rate}%`)
    
  } catch (error) {
    ElMessage.error('检测失败: ' + error.message)
  } finally {
    checking.value = false
  }
}

const batchAugment = async () => {
  if (batchFiles.value.length === 0) return
  
  batchProcessing.value = true
  batchProgress.value = 0
  batchResults.value = []
  
  try {
    const formData = new FormData()
    batchFiles.value.forEach(file => {
      formData.append('files', file.raw)
    })
    
    const operations = {
      resize: batchParams.resize[0] && batchParams.resize[1] ? batchParams.resize : null,
      flip_horizontal: batchParams.flip_horizontal,
      brightness: batchParams.brightness !== 1.0 ? batchParams.brightness : null,
      contrast: batchParams.contrast !== 1.0 ? batchParams.contrast : null
    }
    
    formData.append('operations', JSON.stringify(operations))
    
    const res = await api.batchAugment(formData)
    batchResults.value = res.data.results
    batchProgress.value = 100
    
    ElMessage.success(`批量增强完成，成功 ${res.data.results.filter(r => r.success).length} 张`)
    
  } catch (error) {
    ElMessage.error('批量增强失败: ' + error.message)
  } finally {
    batchProcessing.value = false
  }
}
</script>

<style lang="scss" scoped>
.preprocessing-page {
  h4 {
    font-size: 14px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 15px;
  }
  
  .upload-section {
    margin-bottom: 20px;
  }
  
  .params-section {
    background: #f9f9f9;
    padding: 15px;
    border-radius: 8px;
  }
  
  .param-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }
  
  .preview-section {
    .preview-compare {
      display: flex;
      align-items: center;
      gap: 20px;
      
      .preview-item {
        flex: 1;
        
        .preview-label {
          font-size: 12px;
          color: #909399;
          margin-bottom: 8px;
          text-align: center;
        }
        
        .preview-image {
          border: 1px solid #ebeef5;
          border-radius: 8px;
          overflow: hidden;
          height: 300px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f5f5f5;
          
          img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
          }
        }
      }
      
      .preview-arrow {
        font-size: 24px;
        color: #409EFF;
      }
    }
    
    .result-info {
      margin-top: 15px;
    }
  }
  
  .quality-results {
    .results-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      
      h4 {
        margin-bottom: 0;
      }
      
      .quality-stats {
        display: flex;
        gap: 10px;
      }
    }
  }
  
  .batch-results {
    h4 {
      margin-bottom: 15px;
    }
  }
  
  .file-count {
    margin-top: 10px;
    font-size: 14px;
    color: #409EFF;
  }
}
</style>
