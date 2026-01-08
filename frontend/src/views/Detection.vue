<template>
  <div class="detection-page">
    <div class="page-title">目标检测与标注</div>
    
    <el-row :gutter="20">
      <!-- 左侧：图像画布区域 -->
      <el-col :span="16">
        <div class="content-card canvas-container">
          <!-- 工具栏 -->
          <div class="canvas-toolbar">
            <el-button-group>
              <el-button 
                :type="currentTool === 'select' ? 'primary' : 'default'" 
                @click="currentTool = 'select'"
              >
                <el-icon><Select /></el-icon> 选择
              </el-button>
              <el-button 
                :type="currentTool === 'draw' ? 'primary' : 'default'" 
                @click="currentTool = 'draw'"
              >
                <el-icon><EditPen /></el-icon> 绘制
              </el-button>
            </el-button-group>
            
            <el-button-group class="ml-3">
              <el-button @click="zoomIn" :disabled="!hasImage">
                <el-icon><ZoomIn /></el-icon>
              </el-button>
              <el-button @click="zoomOut" :disabled="!hasImage">
                <el-icon><ZoomOut /></el-icon>
              </el-button>
              <el-button @click="resetZoom" :disabled="!hasImage">
                <el-icon><FullScreen /></el-icon>
              </el-button>
            </el-button-group>
            
            <el-button @click="deleteSelectedBox" :disabled="!selectedAnnotation" type="danger">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
            
            <el-button @click="clearAllAnnotations" :disabled="annotations.length === 0" type="warning">
              <el-icon><DeleteFilled /></el-icon> 清空
            </el-button>
          </div>
          
          <!-- 画布区域 -->
          <div class="canvas-wrapper" ref="canvasWrapper">
            <div 
              v-if="!hasImage" 
              class="upload-area"
              @dragover.prevent="onDragOver"
              @dragleave="onDragLeave"
              @drop.prevent="onDrop"
              :class="{ 'drag-over': isDragOver }"
            >
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleFileSelect"
                accept="image/*"
                drag
              >
                <el-icon class="upload-icon"><UploadFilled /></el-icon>
                <div class="upload-text">
                  <p>将图像拖拽到此处或点击上传</p>
                  <p class="hint">支持 JPG, PNG, BMP, WEBP 格式</p>
                </div>
              </el-upload>
            </div>
            
            <canvas 
              v-show="hasImage"
              ref="canvas"
              @mousedown="onMouseDown"
              @mousemove="onMouseMove"
              @mouseup="onMouseUp"
              @wheel="onWheel"
            ></canvas>
          </div>
          
          <!-- 图像信息 -->
          <div v-if="hasImage" class="image-info">
            <span>尺寸: {{ imageWidth }} × {{ imageHeight }}</span>
            <span>缩放: {{ Math.round(scale * 100) }}%</span>
            <span>标注数: {{ annotations.length }}</span>
            <span v-if="inferenceTime">检测耗时: {{ inferenceTime }}ms</span>
          </div>
        </div>
      </el-col>
      
      <!-- 右侧：控制面板 -->
      <el-col :span="8">
        <!-- 检测参数 -->
        <div class="content-card">
          <h3 class="card-title">检测参数</h3>
          
          <el-form label-position="top" size="small">
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
            :loading="detecting" 
            :disabled="!hasImage"
            @click="runDetection"
            style="width: 100%"
          >
            <el-icon><VideoPlay /></el-icon>
            {{ detecting ? '检测中...' : '开始检测' }}
          </el-button>
        </div>
        
        <!-- 标注列表 -->
        <div class="content-card">
          <h3 class="card-title">
            标注列表
            <el-tag size="small" type="info">{{ annotations.length }}</el-tag>
          </h3>
          
          <div class="annotation-list" v-if="annotations.length > 0">
            <div 
              v-for="(ann, index) in annotations" 
              :key="ann.id"
              class="annotation-item"
              :class="{ active: selectedAnnotation?.id === ann.id }"
              @click="selectAnnotation(ann)"
            >
              <div 
                class="color-indicator" 
                :style="{ backgroundColor: getClassColor(ann.class_id) }"
              ></div>
              <div class="annotation-info">
                <div class="class-name">{{ ann.class_name }}</div>
                <div class="confidence" v-if="ann.confidence">
                  {{ (ann.confidence * 100).toFixed(1) }}%
                </div>
              </div>
              <el-tag v-if="ann.is_manual" size="small" type="warning">手动</el-tag>
              <el-button 
                type="danger" 
                size="small" 
                :icon="Delete"
                circle
                @click.stop="deleteAnnotation(index)"
              />
            </div>
          </div>
          
          <el-empty v-else description="暂无标注" :image-size="60" />
        </div>
        
        <!-- 绘制类别选择 -->
        <div class="content-card" v-if="currentTool === 'draw'">
          <h3 class="card-title">选择类别</h3>
          <el-select 
            v-model="selectedClassId" 
            filterable 
            placeholder="选择要标注的类别"
            style="width: 100%"
          >
            <el-option 
              v-for="cls in classList" 
              :key="cls.id" 
              :label="cls.name" 
              :value="cls.id"
            >
              <span class="class-option">
                <span 
                  class="color-dot" 
                  :style="{ backgroundColor: cls.color }"
                ></span>
                {{ cls.name }}
              </span>
            </el-option>
          </el-select>
        </div>
        
        <!-- 操作按钮 -->
        <div class="content-card">
          <h3 class="card-title">操作</h3>
          <el-space direction="vertical" :fill="true" style="width: 100%">
            <el-button 
              type="success" 
              :disabled="annotations.length === 0"
              @click="saveAnnotations"
              :loading="saving"
            >
              <el-icon><Check /></el-icon> 保存标注
            </el-button>
            
            <el-button @click="showExportDialog = true" :disabled="annotations.length === 0">
              <el-icon><Download /></el-icon> 导出标注
            </el-button>
            
            <el-button @click="resetAll" type="info">
              <el-icon><RefreshRight /></el-icon> 重置
            </el-button>
          </el-space>
        </div>
      </el-col>
    </el-row>
    
    <!-- 导出对话框 -->
    <el-dialog v-model="showExportDialog" title="导出标注" width="400px">
      <el-form label-position="top">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportFormat">
            <el-radio-button value="yolo">YOLO</el-radio-button>
            <el-radio-button value="coco">COCO</el-radio-button>
            <el-radio-button value="voc">VOC</el-radio-button>
            <el-radio-button value="json">JSON</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="exportAnnotations">导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Check, Download, RefreshRight, VideoPlay } from '@element-plus/icons-vue'
import api from '@/api'

// 状态
const canvas = ref(null)
const canvasWrapper = ref(null)
const uploadRef = ref(null)

const hasImage = ref(false)
const imageWidth = ref(0)
const imageHeight = ref(0)
const inferenceTime = ref(null)
const currentImageId = ref(null)
const currentImagePath = ref(null)

const detecting = ref(false)
const saving = ref(false)
const isDragOver = ref(false)

const currentTool = ref('select')  // 'select' | 'draw'
const selectedAnnotation = ref(null)
const selectedClassId = ref(0)

const scale = ref(1)
const offsetX = ref(0)
const offsetY = ref(0)

const annotations = ref([])
const classList = ref([])
const availableWeights = ref([])

const showExportDialog = ref(false)
const exportFormat = ref('yolo')

// 检测参数
const detectParams = reactive({
  weights: 'yolov5s.pt',
  confThreshold: 0.25,
  iouThreshold: 0.45,
  imgSize: 640
})

// 图像对象
let image = null
let ctx = null

// 绘制状态
let isDrawing = false
let isDragging = false
let isResizing = false
let drawStartX = 0
let drawStartY = 0
let dragStartX = 0
let dragStartY = 0
let resizeHandle = null

// 计算属性
const getClassColor = (classId) => {
  const cls = classList.value.find(c => c.id === classId)
  return cls?.color || '#409EFF'
}

const getClassName = (classId) => {
  const cls = classList.value.find(c => c.id === classId)
  return cls?.name || `Class ${classId}`
}

// 初始化
onMounted(async () => {
  // 获取类别列表
  try {
    const res = await api.getClasses()
    classList.value = res.data.classes
  } catch (error) {
    console.error('获取类别列表失败:', error)
  }
  
  // 获取可用权重
  try {
    const res = await api.getWeights()
    availableWeights.value = res.data.weights
    if (availableWeights.value.length > 0) {
      detectParams.weights = availableWeights.value[0]
    }
  } catch (error) {
    console.error('获取权重列表失败:', error)
  }
  
  // 初始化画布
  initCanvas()
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// 初始化画布
const initCanvas = () => {
  if (!canvas.value) return
  ctx = canvas.value.getContext('2d')
  handleResize()
}

// 处理窗口大小变化
const handleResize = () => {
  if (!canvas.value || !canvasWrapper.value) return
  
  const wrapper = canvasWrapper.value
  canvas.value.width = wrapper.clientWidth
  canvas.value.height = wrapper.clientHeight - 40
  
  if (hasImage.value) {
    draw()
  }
}

// 文件选择处理
const handleFileSelect = (uploadFile) => {
  const file = uploadFile.raw
  loadImage(file)
}

// 拖拽处理
const onDragOver = (e) => {
  isDragOver.value = true
}

const onDragLeave = () => {
  isDragOver.value = false
}

const onDrop = (e) => {
  isDragOver.value = false
  const files = e.dataTransfer.files
  if (files.length > 0) {
    loadImage(files[0])
  }
}

// 加载图像
const loadImage = (file) => {
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图像文件')
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    image = new Image()
    image.onload = () => {
      hasImage.value = true
      imageWidth.value = image.width
      imageHeight.value = image.height
      annotations.value = []
      selectedAnnotation.value = null
      inferenceTime.value = null
      currentImageId.value = null
      
      // 保存文件引用用于上传
      currentImagePath.value = file
      
      nextTick(() => {
        fitToCanvas()
        draw()
      })
    }
    image.src = e.target.result
  }
  reader.readAsDataURL(file)
}

// 适应画布
const fitToCanvas = () => {
  if (!canvas.value || !image) return
  
  const canvasWidth = canvas.value.width
  const canvasHeight = canvas.value.height
  
  const scaleX = canvasWidth / image.width
  const scaleY = canvasHeight / image.height
  scale.value = Math.min(scaleX, scaleY, 1) * 0.9
  
  offsetX.value = (canvasWidth - image.width * scale.value) / 2
  offsetY.value = (canvasHeight - image.height * scale.value) / 2
}

// 绘制画布
const draw = () => {
  if (!ctx || !canvas.value) return
  
  // 清空画布
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  
  if (!image) return
  
  // 绘制图像
  ctx.save()
  ctx.translate(offsetX.value, offsetY.value)
  ctx.scale(scale.value, scale.value)
  ctx.drawImage(image, 0, 0)
  
  // 绘制标注框
  annotations.value.forEach((ann, index) => {
    const isSelected = selectedAnnotation.value?.id === ann.id
    drawBoundingBox(ann, isSelected)
  })
  
  // 绘制正在绘制的框
  if (isDrawing && currentTool.value === 'draw') {
    drawTempBox()
  }
  
  ctx.restore()
}

// 绘制边界框
const drawBoundingBox = (ann, isSelected) => {
  const { bbox, class_id, class_name, confidence } = ann
  const color = getClassColor(class_id)
  
  ctx.strokeStyle = color
  ctx.lineWidth = isSelected ? 3 / scale.value : 2 / scale.value
  ctx.strokeRect(bbox.x, bbox.y, bbox.width, bbox.height)
  
  // 填充半透明背景
  ctx.fillStyle = color + '30'
  ctx.fillRect(bbox.x, bbox.y, bbox.width, bbox.height)
  
  // 绘制标签
  const labelText = confidence 
    ? `${class_name} ${(confidence * 100).toFixed(0)}%`
    : class_name
  
  ctx.font = `${14 / scale.value}px Arial`
  const textWidth = ctx.measureText(labelText).width
  const labelHeight = 20 / scale.value
  
  ctx.fillStyle = color
  ctx.fillRect(bbox.x, bbox.y - labelHeight, textWidth + 10 / scale.value, labelHeight)
  
  ctx.fillStyle = '#fff'
  ctx.fillText(labelText, bbox.x + 5 / scale.value, bbox.y - 5 / scale.value)
  
  // 绘制选中状态的调整手柄
  if (isSelected) {
    drawResizeHandles(bbox)
  }
}

// 绘制调整手柄
const drawResizeHandles = (bbox) => {
  const handleSize = 8 / scale.value
  const handles = [
    { x: bbox.x, y: bbox.y },
    { x: bbox.x + bbox.width, y: bbox.y },
    { x: bbox.x, y: bbox.y + bbox.height },
    { x: bbox.x + bbox.width, y: bbox.y + bbox.height }
  ]
  
  ctx.fillStyle = '#fff'
  ctx.strokeStyle = '#409EFF'
  ctx.lineWidth = 2 / scale.value
  
  handles.forEach(h => {
    ctx.beginPath()
    ctx.rect(h.x - handleSize / 2, h.y - handleSize / 2, handleSize, handleSize)
    ctx.fill()
    ctx.stroke()
  })
}

// 绘制临时框
const drawTempBox = () => {
  const color = getClassColor(selectedClassId.value)
  ctx.strokeStyle = color
  ctx.lineWidth = 2 / scale.value
  ctx.setLineDash([5 / scale.value, 5 / scale.value])
  
  const width = (drawStartX - drawStartX) // 这会在鼠标移动时更新
  const height = (drawStartY - drawStartY)
  
  ctx.strokeRect(drawStartX, drawStartY, width, height)
  ctx.setLineDash([])
}

// 鼠标事件处理
const getMousePos = (e) => {
  const rect = canvas.value.getBoundingClientRect()
  const x = (e.clientX - rect.left - offsetX.value) / scale.value
  const y = (e.clientY - rect.top - offsetY.value) / scale.value
  return { x, y }
}

const onMouseDown = (e) => {
  if (!hasImage.value) return
  
  const pos = getMousePos(e)
  
  if (currentTool.value === 'draw') {
    isDrawing = true
    drawStartX = pos.x
    drawStartY = pos.y
  } else {
    // 检查是否点击了调整手柄
    if (selectedAnnotation.value) {
      resizeHandle = getResizeHandle(pos, selectedAnnotation.value.bbox)
      if (resizeHandle) {
        isResizing = true
        return
      }
    }
    
    // 检查是否点击了标注框
    const clickedAnn = findAnnotationAt(pos)
    if (clickedAnn) {
      selectAnnotation(clickedAnn)
      isDragging = true
      dragStartX = pos.x
      dragStartY = pos.y
    } else {
      selectedAnnotation.value = null
    }
  }
  
  draw()
}

const onMouseMove = (e) => {
  if (!hasImage.value) return
  
  const pos = getMousePos(e)
  
  if (isDrawing && currentTool.value === 'draw') {
    // 更新临时框
    ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
    draw()
    
    // 绘制临时框
    ctx.save()
    ctx.translate(offsetX.value, offsetY.value)
    ctx.scale(scale.value, scale.value)
    
    const color = getClassColor(selectedClassId.value)
    ctx.strokeStyle = color
    ctx.lineWidth = 2 / scale.value
    ctx.setLineDash([5 / scale.value, 5 / scale.value])
    ctx.strokeRect(
      Math.min(drawStartX, pos.x),
      Math.min(drawStartY, pos.y),
      Math.abs(pos.x - drawStartX),
      Math.abs(pos.y - drawStartY)
    )
    ctx.setLineDash([])
    ctx.restore()
  }
  
  if (isDragging && selectedAnnotation.value) {
    const dx = pos.x - dragStartX
    const dy = pos.y - dragStartY
    
    selectedAnnotation.value.bbox.x += dx
    selectedAnnotation.value.bbox.y += dy
    
    dragStartX = pos.x
    dragStartY = pos.y
    
    draw()
  }
  
  if (isResizing && selectedAnnotation.value && resizeHandle) {
    resizeAnnotation(selectedAnnotation.value.bbox, resizeHandle, pos)
    draw()
  }
  
  // 更新鼠标样式
  updateCursor(pos)
}

const onMouseUp = (e) => {
  if (isDrawing && currentTool.value === 'draw') {
    const pos = getMousePos(e)
    
    const width = Math.abs(pos.x - drawStartX)
    const height = Math.abs(pos.y - drawStartY)
    
    // 只有当框大于最小尺寸时才创建
    if (width > 10 && height > 10) {
      const newAnnotation = {
        id: Date.now(),
        class_id: selectedClassId.value,
        class_name: getClassName(selectedClassId.value),
        confidence: null,
        is_manual: true,
        bbox: {
          x: Math.min(drawStartX, pos.x),
          y: Math.min(drawStartY, pos.y),
          width,
          height
        }
      }
      
      annotations.value.push(newAnnotation)
      selectAnnotation(newAnnotation)
    }
  }
  
  isDrawing = false
  isDragging = false
  isResizing = false
  resizeHandle = null
  
  draw()
}

const onWheel = (e) => {
  if (!hasImage.value) return
  
  e.preventDefault()
  
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  const newScale = Math.max(0.1, Math.min(5, scale.value * delta))
  
  // 以鼠标位置为中心缩放
  const rect = canvas.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  
  offsetX.value = mouseX - (mouseX - offsetX.value) * (newScale / scale.value)
  offsetY.value = mouseY - (mouseY - offsetY.value) * (newScale / scale.value)
  
  scale.value = newScale
  draw()
}

// 查找点击位置的标注
const findAnnotationAt = (pos) => {
  for (let i = annotations.value.length - 1; i >= 0; i--) {
    const ann = annotations.value[i]
    const { x, y, width, height } = ann.bbox
    
    if (pos.x >= x && pos.x <= x + width && pos.y >= y && pos.y <= y + height) {
      return ann
    }
  }
  return null
}

// 获取调整手柄
const getResizeHandle = (pos, bbox) => {
  const handleSize = 10 / scale.value
  const handles = {
    'nw': { x: bbox.x, y: bbox.y },
    'ne': { x: bbox.x + bbox.width, y: bbox.y },
    'sw': { x: bbox.x, y: bbox.y + bbox.height },
    'se': { x: bbox.x + bbox.width, y: bbox.y + bbox.height }
  }
  
  for (const [key, h] of Object.entries(handles)) {
    if (Math.abs(pos.x - h.x) < handleSize && Math.abs(pos.y - h.y) < handleSize) {
      return key
    }
  }
  return null
}

// 调整标注大小
const resizeAnnotation = (bbox, handle, pos) => {
  switch (handle) {
    case 'nw':
      bbox.width += bbox.x - pos.x
      bbox.height += bbox.y - pos.y
      bbox.x = pos.x
      bbox.y = pos.y
      break
    case 'ne':
      bbox.width = pos.x - bbox.x
      bbox.height += bbox.y - pos.y
      bbox.y = pos.y
      break
    case 'sw':
      bbox.width += bbox.x - pos.x
      bbox.x = pos.x
      bbox.height = pos.y - bbox.y
      break
    case 'se':
      bbox.width = pos.x - bbox.x
      bbox.height = pos.y - bbox.y
      break
  }
  
  // 确保宽高为正
  if (bbox.width < 0) {
    bbox.x += bbox.width
    bbox.width = -bbox.width
  }
  if (bbox.height < 0) {
    bbox.y += bbox.height
    bbox.height = -bbox.height
  }
}

// 更新鼠标样式
const updateCursor = (pos) => {
  if (!selectedAnnotation.value) {
    canvas.value.style.cursor = currentTool.value === 'draw' ? 'crosshair' : 'default'
    return
  }
  
  const handle = getResizeHandle(pos, selectedAnnotation.value.bbox)
  if (handle) {
    const cursors = {
      'nw': 'nw-resize',
      'ne': 'ne-resize',
      'sw': 'sw-resize',
      'se': 'se-resize'
    }
    canvas.value.style.cursor = cursors[handle]
  } else if (findAnnotationAt(pos) === selectedAnnotation.value) {
    canvas.value.style.cursor = 'move'
  } else {
    canvas.value.style.cursor = currentTool.value === 'draw' ? 'crosshair' : 'default'
  }
}

// 选择标注
const selectAnnotation = (ann) => {
  selectedAnnotation.value = ann
  draw()
}

// 删除选中的标注
const deleteSelectedBox = () => {
  if (!selectedAnnotation.value) return
  
  const index = annotations.value.findIndex(a => a.id === selectedAnnotation.value.id)
  if (index > -1) {
    annotations.value.splice(index, 1)
    selectedAnnotation.value = null
    draw()
  }
}

// 删除指定标注
const deleteAnnotation = (index) => {
  annotations.value.splice(index, 1)
  if (selectedAnnotation.value?.id === annotations.value[index]?.id) {
    selectedAnnotation.value = null
  }
  draw()
}

// 清空所有标注
const clearAllAnnotations = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有标注吗？', '提示', {
      type: 'warning'
    })
    annotations.value = []
    selectedAnnotation.value = null
    draw()
  } catch {}
}

// 缩放操作
const zoomIn = () => {
  scale.value = Math.min(5, scale.value * 1.2)
  draw()
}

const zoomOut = () => {
  scale.value = Math.max(0.1, scale.value / 1.2)
  draw()
}

const resetZoom = () => {
  fitToCanvas()
  draw()
}

// 执行检测
const runDetection = async () => {
  if (!currentImagePath.value) return
  
  detecting.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', currentImagePath.value)
    formData.append('conf_threshold', detectParams.confThreshold)
    formData.append('iou_threshold', detectParams.iouThreshold)
    formData.append('img_size', detectParams.imgSize)
    formData.append('weights', detectParams.weights)
    
    const res = await api.detect(formData)
    const result = res.data
    
    currentImageId.value = result.image_id
    inferenceTime.value = result.inference_time
    
    // 将检测结果转换为标注
    annotations.value = result.detections.map(det => ({
      ...det,
      is_manual: false
    }))
    
    ElMessage.success(`检测完成，发现 ${annotations.value.length} 个目标`)
    draw()
    
  } catch (error) {
    ElMessage.error('检测失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    detecting.value = false
  }
}

// 保存标注
const saveAnnotations = async () => {
  if (!currentImageId.value) {
    // 如果还没有 imageId，需要先上传图像执行检测
    ElMessage.warning('请先执行检测')
    return
  }
  
  saving.value = true
  
  try {
    await api.saveAnnotations({
      image_id: currentImageId.value,
      image_path: `/uploads/images/${currentImageId.value}`,
      image_width: imageWidth.value,
      image_height: imageHeight.value,
      annotations: annotations.value.map(ann => ({
        id: ann.id,
        class_id: ann.class_id,
        class_name: ann.class_name,
        bbox: ann.bbox,
        is_manual: ann.is_manual,
        confidence: ann.confidence
      }))
    })
    
    ElMessage.success('标注保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 导出标注
const exportAnnotations = async () => {
  if (!currentImageId.value) {
    ElMessage.warning('请先保存标注')
    return
  }
  
  try {
    const res = await api.exportAnnotations({
      image_ids: [currentImageId.value],
      format: exportFormat.value
    })
    
    ElMessage.success('导出成功')
    showExportDialog.value = false
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 重置
const resetAll = () => {
  hasImage.value = false
  image = null
  annotations.value = []
  selectedAnnotation.value = null
  currentImageId.value = null
  currentImagePath.value = null
  inferenceTime.value = null
  scale.value = 1
  offsetX.value = 0
  offsetY.value = 0
  
  if (ctx) {
    ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  }
}

// 监听工具变化
watch(currentTool, () => {
  if (currentTool.value === 'draw') {
    selectedAnnotation.value = null
    draw()
  }
})
</script>

<style lang="scss" scoped>
.detection-page {
  height: 100%;
}

.canvas-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 160px);
  min-height: 500px;
}

.canvas-toolbar {
  display: flex;
  gap: 10px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
  flex-wrap: wrap;
  
  .ml-3 {
    margin-left: 12px;
  }
}

.canvas-wrapper {
  flex: 1;
  position: relative;
  background: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 15px;
  
  canvas {
    display: block;
  }
}

.upload-area {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &.drag-over {
    background: rgba(64, 158, 255, 0.1);
    border: 2px dashed #409EFF;
  }
  
  :deep(.el-upload-dragger) {
    width: 400px;
    height: 250px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  
  .upload-icon {
    font-size: 60px;
    color: #909399;
    margin-bottom: 20px;
  }
  
  .upload-text {
    text-align: center;
    
    p {
      margin: 5px 0;
      color: #606266;
    }
    
    .hint {
      color: #909399;
      font-size: 12px;
    }
  }
}

.image-info {
  display: flex;
  gap: 20px;
  padding-top: 10px;
  font-size: 12px;
  color: #909399;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.annotation-list {
  max-height: 300px;
  overflow-y: auto;
}

.annotation-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
  
  &:hover {
    background: #f5f5f5;
  }
  
  &.active {
    background: #ecf5ff;
    border: 1px solid #409EFF;
  }
  
  .color-indicator {
    width: 12px;
    height: 12px;
    border-radius: 2px;
  }
  
  .annotation-info {
    flex: 1;
    
    .class-name {
      font-size: 14px;
      color: #303133;
    }
    
    .confidence {
      font-size: 12px;
      color: #909399;
    }
  }
}

.class-option {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .color-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }
}
</style>
