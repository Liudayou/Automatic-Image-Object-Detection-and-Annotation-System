<template>
  <div class="dataset-page">
    <div class="page-title">数据集管理</div>
    
    <el-row :gutter="20">
      <!-- 左侧：数据集列表 -->
      <el-col :span="8">
        <div class="content-card">
          <div class="card-header">
            <h3 class="card-title">数据集列表</h3>
            <el-button type="primary" size="small" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon> 新建
            </el-button>
          </div>
          
          <div class="dataset-list" v-loading="loading">
            <div 
              v-for="dataset in datasets" 
              :key="dataset.path"
              class="dataset-item"
              :class="{ active: selectedDataset?.path === dataset.path }"
              @click="selectDataset(dataset)"
            >
              <div class="dataset-icon">
                <el-icon><FolderOpened /></el-icon>
              </div>
              <div class="dataset-info">
                <div class="dataset-name">{{ dataset.name }}</div>
                <div class="dataset-meta">
                  <el-tag size="small" :type="getTypeTag(dataset.type)">
                    {{ dataset.type }}
                  </el-tag>
                  <span>{{ dataset.num_classes }} 类</span>
                </div>
              </div>
            </div>
            
            <el-empty v-if="datasets.length === 0" description="暂无数据集" />
          </div>
        </div>
      </el-col>
      
      <!-- 右侧：数据集详情 -->
      <el-col :span="16">
        <div v-if="selectedDataset" class="content-card">
          <div class="card-header">
            <h3 class="card-title">{{ selectedDataset.name }}</h3>
            <el-space>
              <el-button 
                v-if="selectedDataset.type === 'custom'"
                type="danger" 
                size="small"
                @click="deleteDataset"
              >
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </el-space>
          </div>
          
          <!-- 基本信息 -->
          <el-descriptions :column="2" border>
            <el-descriptions-item label="数据集名称">{{ datasetDetail?.name }}</el-descriptions-item>
            <el-descriptions-item label="类别数量">{{ datasetDetail?.num_classes }}</el-descriptions-item>
            <el-descriptions-item label="训练集">{{ datasetDetail?.split?.train || 0 }} 张</el-descriptions-item>
            <el-descriptions-item label="验证集">{{ datasetDetail?.split?.val || 0 }} 张</el-descriptions-item>
            <el-descriptions-item label="测试集">{{ datasetDetail?.split?.test || 0 }} 张</el-descriptions-item>
            <el-descriptions-item label="配置路径">{{ datasetDetail?.path }}</el-descriptions-item>
          </el-descriptions>
          
          <!-- 类别列表 -->
          <h4 style="margin: 20px 0 10px;">类别列表</h4>
          <div class="class-tags">
            <el-tag 
              v-for="(cls, index) in datasetDetail?.classes || []" 
              :key="index"
              size="small"
            >
              {{ index }}: {{ cls }}
            </el-tag>
          </div>
          
          <!-- 上传图像（仅自定义数据集） -->
          <template v-if="selectedDataset.type === 'custom'">
            <h4 style="margin: 20px 0 10px;">上传图像</h4>
            <el-form inline>
              <el-form-item label="目标划分">
                <el-select v-model="uploadSplit" size="small">
                  <el-option value="train" label="训练集" />
                  <el-option value="val" label="验证集" />
                  <el-option value="test" label="测试集" />
                </el-select>
              </el-form-item>
            </el-form>
            
            <el-upload
              v-model:file-list="uploadFiles"
              :auto-upload="false"
              multiple
              accept="image/*"
              drag
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">拖拽图像到此处或点击上传</div>
            </el-upload>
            
            <el-button 
              type="primary" 
              :loading="uploading"
              :disabled="uploadFiles.length === 0"
              @click="uploadImages"
              style="margin-top: 10px;"
            >
              上传 {{ uploadFiles.length }} 个文件
            </el-button>
          </template>
          
          <!-- 图像预览 -->
          <h4 style="margin: 20px 0 10px;">
            图像预览
            <el-select v-model="previewSplit" size="small" style="margin-left: 10px;">
              <el-option value="train" label="训练集" />
              <el-option value="val" label="验证集" />
              <el-option value="test" label="测试集" />
            </el-select>
          </h4>
          
          <div class="image-preview" v-loading="loadingImages">
            <div 
              v-for="img in previewImages" 
              :key="img.path"
              class="preview-item"
            >
              <img :src="getImageUrl(img.path)" @error="handleImageError" />
              <div class="image-name">{{ img.name }}</div>
            </div>
            <el-empty v-if="previewImages.length === 0" description="暂无图像" />
          </div>
          
          <el-pagination
            v-if="imageTotal > 0"
            :current-page="imagePage"
            :page-size="imagePageSize"
            :total="imageTotal"
            layout="prev, pager, next"
            @current-change="handlePageChange"
            style="margin-top: 15px;"
          />
        </div>
        
        <div v-else class="content-card empty-detail">
          <el-empty description="请选择一个数据集查看详情" />
        </div>
      </el-col>
    </el-row>
    
    <!-- 新建数据集对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建数据集" width="500px">
      <el-form 
        ref="createFormRef"
        :model="createForm" 
        :rules="createRules"
        label-position="top"
      >
        <el-form-item label="数据集名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入数据集名称" />
        </el-form-item>
        
        <el-form-item label="类别列表" prop="classes">
          <el-input 
            v-model="createForm.classes" 
            type="textarea"
            :rows="4"
            placeholder="每行一个类别名称，或用逗号分隔"
          />
          <div class="form-tip">例如：person, car, dog 或每行一个</div>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input 
            v-model="createForm.description" 
            type="textarea"
            :rows="2"
            placeholder="数据集描述（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createDataset" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const creating = ref(false)
const uploading = ref(false)
const loadingImages = ref(false)

const datasets = ref([])
const selectedDataset = ref(null)
const datasetDetail = ref(null)

const showCreateDialog = ref(false)
const createFormRef = ref(null)

const uploadFiles = ref([])
const uploadSplit = ref('train')

const previewSplit = ref('train')
const previewImages = ref([])
const imagePage = ref(1)
const imagePageSize = ref(12)
const imageTotal = ref(0)

const createForm = reactive({
  name: '',
  classes: '',
  description: ''
})

const createRules = {
  name: [{ required: true, message: '请输入数据集名称', trigger: 'blur' }],
  classes: [{ required: true, message: '请输入类别列表', trigger: 'blur' }]
}

onMounted(() => {
  loadDatasets()
})

watch(selectedDataset, async (val) => {
  if (val) {
    await loadDatasetDetail()
    await loadImages()
  }
})

watch(previewSplit, () => {
  imagePage.value = 1
  loadImages()
})

const loadDatasets = async () => {
  loading.value = true
  try {
    const res = await api.listDatasets()
    datasets.value = res.data.datasets
  } catch (error) {
    console.error('加载数据集失败:', error)
  } finally {
    loading.value = false
  }
}

const selectDataset = (dataset) => {
  selectedDataset.value = dataset
  previewSplit.value = 'train'
  imagePage.value = 1
}

const loadDatasetDetail = async () => {
  if (!selectedDataset.value) return
  
  try {
    const res = await api.getDatasetInfo(selectedDataset.value.name)
    datasetDetail.value = res.data
  } catch (error) {
    console.error('加载数据集详情失败:', error)
  }
}

const loadImages = async () => {
  if (!selectedDataset.value) return
  
  loadingImages.value = true
  try {
    const res = await api.listDatasetImages(
      selectedDataset.value.name,
      previewSplit.value,
      imagePage.value,
      imagePageSize.value
    )
    previewImages.value = res.data.images
    imageTotal.value = res.data.total
  } catch (error) {
    console.error('加载图像失败:', error)
    previewImages.value = []
  } finally {
    loadingImages.value = false
  }
}

const handlePageChange = (page) => {
  imagePage.value = page
  loadImages()
}

const createDataset = async () => {
  const valid = await createFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  creating.value = true
  
  try {
    const formData = new FormData()
    formData.append('name', createForm.name)
    formData.append('classes', createForm.classes.replace(/\n/g, ','))
    if (createForm.description) {
      formData.append('description', createForm.description)
    }
    
    await api.createDataset(formData)
    
    ElMessage.success('数据集创建成功')
    showCreateDialog.value = false
    
    // 重置表单
    createForm.name = ''
    createForm.classes = ''
    createForm.description = ''
    
    await loadDatasets()
    
  } catch (error) {
    ElMessage.error('创建失败: ' + error.message)
  } finally {
    creating.value = false
  }
}

const deleteDataset = async () => {
  if (!selectedDataset.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除数据集 "${selectedDataset.value.name}" 吗？此操作不可恢复。`,
      '确认删除',
      { type: 'warning' }
    )
    
    await api.deleteDataset(selectedDataset.value.name)
    
    ElMessage.success('删除成功')
    selectedDataset.value = null
    datasetDetail.value = null
    await loadDatasets()
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

const uploadImages = async () => {
  if (uploadFiles.value.length === 0) return
  
  uploading.value = true
  
  try {
    const formData = new FormData()
    uploadFiles.value.forEach(file => {
      formData.append('files', file.raw)
    })
    
    await api.uploadDatasetImages(
      selectedDataset.value.name,
      formData,
      uploadSplit.value
    )
    
    ElMessage.success('上传成功')
    uploadFiles.value = []
    
    // 刷新数据
    await loadDatasetDetail()
    await loadImages()
    
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  } finally {
    uploading.value = false
  }
}

const getTypeTag = (type) => {
  const types = {
    'coco': 'primary',
    'voc': 'success',
    'custom': 'warning'
  }
  return types[type] || 'info'
}

const getImageUrl = (path) => {
  // 如果已经是URL路径，直接返回
  if (path.startsWith('/') || path.startsWith('http')) {
    return path
  }
  // 否则构建URL
  return `/api${path}`
}

const handleImageError = (e) => {
  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iIGZpbGw9IiM5OTkiPuWbvuWDj+aXoOazleWKoOi9vTwvdGV4dD48L3N2Zz4='
}
</script>

<style lang="scss" scoped>
.dataset-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    
    .card-title {
      margin-bottom: 0;
    }
  }
  
  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
  
  .dataset-list {
    max-height: 600px;
    overflow-y: auto;
  }
  
  .dataset-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      background: #f5f5f5;
    }
    
    &.active {
      background: #ecf5ff;
      border: 1px solid #409EFF;
    }
    
    .dataset-icon {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #409EFF, #66b1ff);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .el-icon {
        font-size: 20px;
        color: #fff;
      }
    }
    
    .dataset-info {
      flex: 1;
      
      .dataset-name {
        font-size: 14px;
        font-weight: 500;
        color: #303133;
      }
      
      .dataset-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 4px;
        font-size: 12px;
        color: #909399;
      }
    }
  }
  
  .class-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    max-height: 100px;
    overflow-y: auto;
  }
  
  .image-preview {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 10px;
    max-height: 300px;
    overflow-y: auto;
    
    .preview-item {
      border: 1px solid #ebeef5;
      border-radius: 4px;
      overflow: hidden;
      
      img {
        width: 100%;
        height: 80px;
        object-fit: cover;
      }
      
      .image-name {
        padding: 4px;
        font-size: 10px;
        color: #909399;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }
  
  .empty-detail {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 400px;
  }
  
  .form-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }
}
</style>
