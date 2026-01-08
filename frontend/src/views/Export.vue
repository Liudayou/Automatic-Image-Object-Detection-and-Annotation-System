<template>
  <div class="export-page">
    <div class="page-title">导出管理</div>
    
    <el-row :gutter="20">
      <!-- 左侧：标注列表 -->
      <el-col :span="10">
        <div class="content-card">
          <div class="card-header">
            <h3 class="card-title">已保存标注</h3>
            <el-button 
              type="primary" 
              size="small"
              :disabled="selectedIds.length === 0"
              @click="showExportDialog = true"
            >
              <el-icon><Download /></el-icon>
              导出选中 ({{ selectedIds.length }})
            </el-button>
          </div>
          
          <el-table 
            :data="annotations" 
            v-loading="loading"
            @selection-change="handleSelectionChange"
            max-height="500"
          >
            <el-table-column type="selection" width="50" />
            <el-table-column prop="image_id" label="图像ID" width="120">
              <template #default="{ row }">
                {{ row.image_id.substring(0, 8) }}...
              </template>
            </el-table-column>
            <el-table-column prop="annotation_count" label="标注数" width="80" />
            <el-table-column prop="updated_at" label="更新时间">
              <template #default="{ row }">
                {{ formatTime(row.updated_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" size="small" text @click="viewAnnotation(row)">
                  查看
                </el-button>
                <el-button type="danger" size="small" text @click="deleteAnnotation(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-pagination
            :current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            @current-change="handlePageChange"
            style="margin-top: 15px;"
          />
        </div>
      </el-col>
      
      <!-- 右侧：导出历史和快捷操作 -->
      <el-col :span="14">
        <div class="content-card">
          <h3 class="card-title">快捷导出</h3>
          
          <el-row :gutter="15">
            <el-col :span="6" v-for="format in exportFormats" :key="format.value">
              <div 
                class="format-card"
                :class="{ active: quickExportFormat === format.value }"
                @click="quickExportFormat = format.value"
              >
                <el-icon class="format-icon"><Document /></el-icon>
                <div class="format-name">{{ format.label }}</div>
                <div class="format-desc">{{ format.description }}</div>
              </div>
            </el-col>
          </el-row>
          
          <div class="export-options">
            <el-checkbox v-model="includeImages">包含图像文件</el-checkbox>
          </div>
          
          <el-button 
            type="primary" 
            size="large"
            :loading="exporting"
            :disabled="selectedIds.length === 0"
            @click="quickExport"
            style="width: 100%; margin-top: 15px;"
          >
            <el-icon><Download /></el-icon>
            导出 {{ selectedIds.length }} 个标注为 {{ getFormatLabel(quickExportFormat) }}
          </el-button>
        </div>
        
        <div class="content-card">
          <div class="card-header">
            <h3 class="card-title">导出记录</h3>
            <el-button size="small" @click="cleanExports" :loading="cleaning">
              <el-icon><Delete /></el-icon> 清理
            </el-button>
          </div>
          
          <el-timeline v-if="exportHistory.length > 0">
            <el-timeline-item 
              v-for="(item, index) in exportHistory" 
              :key="index"
              :timestamp="item.time"
              placement="top"
            >
              <el-card>
                <p>
                  导出 <strong>{{ item.count }}</strong> 个标注
                  为 <el-tag size="small">{{ item.format }}</el-tag> 格式
                </p>
                <p class="export-path">{{ item.path }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          
          <el-empty v-else description="暂无导出记录" />
        </div>
      </el-col>
    </el-row>
    
    <!-- 导出对话框 -->
    <el-dialog v-model="showExportDialog" title="导出设置" width="500px">
      <el-form label-position="top">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportFormat">
            <el-radio-button 
              v-for="format in exportFormats" 
              :key="format.value"
              :value="format.value"
            >
              {{ format.label }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="includeImages">包含图像文件</el-checkbox>
          <div class="form-tip">勾选后将下载包含图像的压缩包</div>
        </el-form-item>
        
        <el-alert 
          type="info" 
          :closable="false"
          style="margin-top: 10px;"
        >
          将导出 {{ selectedIds.length }} 个标注文件
        </el-alert>
      </el-form>
      
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="doExport" :loading="exporting">
          开始导出
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 标注详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="标注详情" width="700px">
      <div v-if="selectedAnnotation">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="图像ID">{{ selectedAnnotation.image_id }}</el-descriptions-item>
          <el-descriptions-item label="图像尺寸">
            {{ selectedAnnotation.image_width }} × {{ selectedAnnotation.image_height }}
          </el-descriptions-item>
          <el-descriptions-item label="标注数量">{{ selectedAnnotation.annotations?.length || 0 }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatTime(selectedAnnotation.updated_at) }}</el-descriptions-item>
        </el-descriptions>
        
        <h4 style="margin: 15px 0;">标注列表</h4>
        <el-table :data="selectedAnnotation.annotations" size="small" max-height="300">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="class_name" label="类别" />
          <el-table-column label="置信度" width="80">
            <template #default="{ row }">
              {{ row.confidence ? (row.confidence * 100).toFixed(1) + '%' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="位置">
            <template #default="{ row }">
              ({{ Math.round(row.bbox.x) }}, {{ Math.round(row.bbox.y) }}) 
              {{ Math.round(row.bbox.width) }}×{{ Math.round(row.bbox.height) }}
            </template>
          </el-table-column>
          <el-table-column label="类型" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_manual ? 'warning' : 'success'" size="small">
                {{ row.is_manual ? '手动' : '自动' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const exporting = ref(false)
const cleaning = ref(false)

const annotations = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const selectedIds = ref([])
const selectedAnnotation = ref(null)

const showExportDialog = ref(false)
const showDetailDialog = ref(false)

const exportFormat = ref('yolo')
const quickExportFormat = ref('yolo')
const includeImages = ref(false)

const exportFormats = ref([
  { value: 'yolo', label: 'YOLO', description: 'TXT格式标注' },
  { value: 'coco', label: 'COCO', description: 'JSON格式' },
  { value: 'voc', label: 'VOC', description: 'XML格式' },
  { value: 'json', label: 'JSON', description: '原始JSON' }
])

const exportHistory = ref([])

onMounted(async () => {
  await loadAnnotations()
  await loadExportFormats()
})

const loadAnnotations = async () => {
  loading.value = true
  try {
    const res = await api.listAnnotations(page.value, pageSize.value)
    annotations.value = res.data.items
    total.value = res.data.total
  } catch (error) {
    console.error('加载标注列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadExportFormats = async () => {
  try {
    const res = await api.getExportFormats()
    exportFormats.value = res.data.formats
  } catch (error) {
    console.error('加载导出格式失败:', error)
  }
}

const handlePageChange = (p) => {
  page.value = p
  loadAnnotations()
}

const handleSelectionChange = (selection) => {
  selectedIds.value = selection.map(item => item.image_id)
}

const viewAnnotation = async (row) => {
  try {
    const res = await api.getAnnotations(row.image_id)
    selectedAnnotation.value = res.data
    showDetailDialog.value = true
  } catch (error) {
    ElMessage.error('加载标注详情失败')
  }
}

const deleteAnnotation = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个标注吗？', '确认删除', { type: 'warning' })
    await api.deleteAnnotations(row.image_id)
    ElMessage.success('删除成功')
    await loadAnnotations()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const quickExport = () => {
  exportFormat.value = quickExportFormat.value
  doExport()
}

const doExport = async () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择要导出的标注')
    return
  }
  
  exporting.value = true
  
  try {
    const res = await api.exportAnnotations({
      image_ids: selectedIds.value,
      format: exportFormat.value,
      include_images: includeImages.value
    })
    
    ElMessage.success('导出成功')
    showExportDialog.value = false
    
    // 添加到导出历史
    exportHistory.value.unshift({
      time: new Date().toLocaleString('zh-CN'),
      count: selectedIds.value.length,
      format: exportFormat.value.toUpperCase(),
      path: res.data.output_dir
    })
    
    // 只保留最近10条记录
    if (exportHistory.value.length > 10) {
      exportHistory.value = exportHistory.value.slice(0, 10)
    }
    
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  } finally {
    exporting.value = false
  }
}

const cleanExports = async () => {
  try {
    await ElMessageBox.confirm('确定要清理所有导出文件吗？', '确认清理', { type: 'warning' })
    
    cleaning.value = true
    // 这里可以调用清理 API
    exportHistory.value = []
    ElMessage.success('清理完成')
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清理失败')
    }
  } finally {
    cleaning.value = false
  }
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const getFormatLabel = (value) => {
  const format = exportFormats.value.find(f => f.value === value)
  return format?.label || value
}
</script>

<style lang="scss" scoped>
.export-page {
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
  
  .format-card {
    padding: 20px 15px;
    border: 2px solid #ebeef5;
    border-radius: 8px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      border-color: #409EFF;
    }
    
    &.active {
      border-color: #409EFF;
      background: #ecf5ff;
    }
    
    .format-icon {
      font-size: 32px;
      color: #409EFF;
      margin-bottom: 10px;
    }
    
    .format-name {
      font-size: 16px;
      font-weight: 500;
      color: #303133;
      margin-bottom: 5px;
    }
    
    .format-desc {
      font-size: 12px;
      color: #909399;
    }
  }
  
  .export-options {
    margin-top: 20px;
    padding: 15px;
    background: #f5f7fa;
    border-radius: 4px;
  }
  
  .form-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }
  
  .export-path {
    font-size: 12px;
    color: #909399;
    margin-top: 5px;
    word-break: break-all;
  }
}
</style>
