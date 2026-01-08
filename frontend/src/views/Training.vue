<template>
  <div class="training-page">
    <div class="page-title">模型训练</div>
    
    <el-row :gutter="20">
      <!-- 左侧：训练配置 -->
      <el-col :span="10">
        <div class="content-card">
          <h3 class="card-title">训练配置</h3>
          
          <el-form 
            ref="formRef"
            :model="trainConfig" 
            :rules="rules"
            label-position="top"
          >
            <el-form-item label="预训练权重" prop="weights">
              <el-select v-model="trainConfig.weights" style="width: 100%">
                <el-option 
                  v-for="w in availableWeights" 
                  :key="w" 
                  :label="w" 
                  :value="w" 
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="数据集配置" prop="data_yaml">
              <el-select v-model="trainConfig.data_yaml" style="width: 100%">
                <el-option 
                  v-for="d in availableDatasets" 
                  :key="d.path" 
                  :label="d.name" 
                  :value="d.relative_path || d.path" 
                />
              </el-select>
            </el-form-item>
            
            <el-row :gutter="15">
              <el-col :span="12">
                <el-form-item label="训练轮数" prop="epochs">
                  <el-input-number 
                    v-model="trainConfig.epochs" 
                    :min="1" 
                    :max="1000"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="批次大小" prop="batch_size">
                  <el-input-number 
                    v-model="trainConfig.batch_size" 
                    :min="1" 
                    :max="128"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="15">
              <el-col :span="12">
                <el-form-item label="图像尺寸" prop="img_size">
                  <el-select v-model="trainConfig.img_size" style="width: 100%">
                    <el-option :value="320" label="320" />
                    <el-option :value="416" label="416" />
                    <el-option :value="640" label="640" />
                    <el-option :value="1280" label="1280" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="优化器" prop="optimizer">
                  <el-select v-model="trainConfig.optimizer" style="width: 100%">
                    <el-option value="SGD" label="SGD" />
                    <el-option value="Adam" label="Adam" />
                    <el-option value="AdamW" label="AdamW" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="15">
              <el-col :span="12">
                <el-form-item label="学习率" prop="learning_rate">
                  <el-input-number 
                    v-model="trainConfig.learning_rate" 
                    :min="0.0001" 
                    :max="0.1"
                    :step="0.001"
                    :precision="4"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="早停耐心值" prop="patience">
                  <el-input-number 
                    v-model="trainConfig.patience" 
                    :min="0" 
                    :max="500"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="实验名称" prop="name">
              <el-input v-model="trainConfig.name" placeholder="exp" />
            </el-form-item>
            
            <el-form-item label="训练设备" prop="device">
              <el-radio-group v-model="trainConfig.device">
                <el-radio-button value="">自动</el-radio-button>
                <el-radio-button value="0">GPU 0</el-radio-button>
                <el-radio-button value="cpu">CPU</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-form>
          
          <el-button 
            type="primary" 
            size="large"
            :loading="starting"
            @click="startTraining"
            style="width: 100%"
          >
            <el-icon><VideoPlay /></el-icon>
            开始训练
          </el-button>
        </div>
      </el-col>
      
      <!-- 右侧：训练任务列表和状态 -->
      <el-col :span="14">
        <!-- 当前训练状态 -->
        <div class="content-card" v-if="currentTask">
          <h3 class="card-title">
            当前训练
            <el-tag :type="getStatusType(currentTask.status)" size="small">
              {{ getStatusText(currentTask.status) }}
            </el-tag>
          </h3>
          
          <div class="training-progress">
            <div class="progress-info">
              <span>Epoch {{ currentTask.current_epoch }} / {{ currentTask.total_epochs }}</span>
              <span>{{ currentTask.progress.toFixed(1) }}%</span>
            </div>
            <el-progress 
              :percentage="currentTask.progress" 
              :status="currentTask.status === 'completed' ? 'success' : ''"
            />
          </div>
          
          <div class="training-output" v-if="trainingOutput.length > 0">
            <h4>训练日志</h4>
            <div class="output-container" ref="outputContainer">
              <div v-for="(line, i) in trainingOutput" :key="i" class="output-line">
                {{ line }}
              </div>
            </div>
          </div>
          
          <el-button 
            v-if="currentTask.status === 'running'"
            type="danger" 
            @click="stopTraining"
            :loading="stopping"
          >
            <el-icon><VideoPause /></el-icon>
            停止训练
          </el-button>
          
          <el-button 
            v-if="currentTask.status === 'completed'"
            type="success" 
            @click="viewResults"
          >
            <el-icon><View /></el-icon>
            查看结果
          </el-button>
        </div>
        
        <!-- 训练历史 -->
        <div class="content-card">
          <h3 class="card-title">训练历史</h3>
          
          <el-table :data="trainingTasks" v-loading="loadingTasks">
            <el-table-column prop="task_id" label="任务ID" width="100">
              <template #default="{ row }">
                {{ row.task_id.substring(0, 8) }}...
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="progress" label="进度" width="150">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.progress" 
                  :show-text="false"
                  :status="row.status === 'completed' ? 'success' : ''"
                />
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button 
                  v-if="row.status === 'running'"
                  type="primary" 
                  size="small" 
                  text
                  @click="selectTask(row)"
                >
                  查看
                </el-button>
                <el-button 
                  v-if="row.status === 'completed'"
                  type="success" 
                  size="small" 
                  text
                  @click="viewTaskResults(row)"
                >
                  结果
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
    
    <!-- 训练结果对话框 -->
    <el-dialog v-model="showResultsDialog" title="训练结果" width="800px">
      <div v-if="trainingResults">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ trainingResults.task_id }}</el-descriptions-item>
          <el-descriptions-item label="结果目录">{{ trainingResults.results_dir }}</el-descriptions-item>
        </el-descriptions>
        
        <h4 style="margin: 20px 0 10px;">模型权重</h4>
        <el-table :data="Object.entries(trainingResults.weights || {})" size="small">
          <el-table-column label="文件">
            <template #default="{ row }">{{ row[0] }}</template>
          </el-table-column>
          <el-table-column label="路径">
            <template #default="{ row }">{{ row[1] }}</template>
          </el-table-column>
        </el-table>
        
        <h4 style="margin: 20px 0 10px;">训练曲线</h4>
        <div class="plots-grid" v-if="trainingResults.plots?.length > 0">
          <img 
            v-for="(plot, i) in trainingResults.plots" 
            :key="i" 
            :src="'file://' + plot"
            @error="handlePlotError"
          />
        </div>
        <el-empty v-else description="暂无图表" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const formRef = ref(null)
const outputContainer = ref(null)

const starting = ref(false)
const stopping = ref(false)
const loadingTasks = ref(false)

const availableWeights = ref([])
const availableDatasets = ref([])
const trainingTasks = ref([])
const currentTask = ref(null)
const trainingOutput = ref([])
const trainingResults = ref(null)
const showResultsDialog = ref(false)

let pollTimer = null

const trainConfig = reactive({
  weights: 'yolov5s.pt',
  data_yaml: '',
  epochs: 100,
  batch_size: 16,
  img_size: 640,
  learning_rate: 0.01,
  project: 'runs/train',
  name: 'exp',
  device: '',
  workers: 8,
  patience: 100,
  optimizer: 'SGD'
})

const rules = {
  weights: [{ required: true, message: '请选择预训练权重', trigger: 'change' }],
  data_yaml: [{ required: true, message: '请选择数据集配置', trigger: 'change' }],
  epochs: [{ required: true, message: '请输入训练轮数', trigger: 'blur' }],
  batch_size: [{ required: true, message: '请输入批次大小', trigger: 'blur' }]
}

onMounted(async () => {
  await loadData()
  await loadTasks()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

const loadData = async () => {
  try {
    const [weightsRes, datasetsRes] = await Promise.all([
      api.getWeights(),
      api.getDatasets()
    ])
    
    availableWeights.value = weightsRes.data.weights
    availableDatasets.value = datasetsRes.data.datasets
    
    if (availableWeights.value.length > 0) {
      trainConfig.weights = availableWeights.value[0]
    }
    if (availableDatasets.value.length > 0) {
      trainConfig.data_yaml = availableDatasets.value[0].relative_path || availableDatasets.value[0].path
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const loadTasks = async () => {
  loadingTasks.value = true
  try {
    const res = await api.listTrainingTasks()
    trainingTasks.value = res.data.tasks
    
    // 自动选择正在运行的任务
    const runningTask = trainingTasks.value.find(t => t.status === 'running')
    if (runningTask) {
      selectTask(runningTask)
    }
  } catch (error) {
    console.error('加载任务列表失败:', error)
  } finally {
    loadingTasks.value = false
  }
}

const startPolling = () => {
  pollTimer = setInterval(async () => {
    if (currentTask.value && ['pending', 'running'].includes(currentTask.value.status)) {
      await updateTaskStatus()
    }
    await loadTasks()
  }, 3000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const updateTaskStatus = async () => {
  if (!currentTask.value) return
  
  try {
    const [statusRes, outputRes] = await Promise.all([
      api.getTrainingStatus(currentTask.value.task_id),
      api.getTrainingOutput(currentTask.value.task_id)
    ])
    
    currentTask.value = statusRes.data
    trainingOutput.value = outputRes.data.output
    
    // 自动滚动到底部
    nextTick(() => {
      if (outputContainer.value) {
        outputContainer.value.scrollTop = outputContainer.value.scrollHeight
      }
    })
  } catch (error) {
    console.error('更新任务状态失败:', error)
  }
}

const startTraining = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  starting.value = true
  
  try {
    const res = await api.startTraining(trainConfig)
    ElMessage.success('训练任务已创建')
    
    currentTask.value = {
      task_id: res.data.task_id,
      status: 'pending',
      progress: 0,
      current_epoch: 0,
      total_epochs: trainConfig.epochs
    }
    
    trainingOutput.value = []
    await loadTasks()
    
  } catch (error) {
    ElMessage.error('创建训练任务失败: ' + error.message)
  } finally {
    starting.value = false
  }
}

const stopTraining = async () => {
  if (!currentTask.value) return
  
  stopping.value = true
  
  try {
    await api.stopTraining(currentTask.value.task_id)
    ElMessage.success('训练已停止')
    await updateTaskStatus()
  } catch (error) {
    ElMessage.error('停止训练失败: ' + error.message)
  } finally {
    stopping.value = false
  }
}

const selectTask = (task) => {
  currentTask.value = task
  trainingOutput.value = []
  updateTaskStatus()
}

const viewResults = () => {
  if (currentTask.value) {
    viewTaskResults(currentTask.value)
  }
}

const viewTaskResults = async (task) => {
  try {
    const res = await api.getTrainingResults(task.task_id)
    trainingResults.value = res.data
    showResultsDialog.value = true
  } catch (error) {
    ElMessage.error('获取训练结果失败: ' + error.message)
  }
}

const getStatusType = (status) => {
  const types = {
    'pending': 'info',
    'running': 'primary',
    'completed': 'success',
    'failed': 'danger',
    'stopped': 'warning'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'pending': '等待中',
    'running': '训练中',
    'completed': '已完成',
    'failed': '失败',
    'stopped': '已停止'
  }
  return texts[status] || status
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const handlePlotError = (e) => {
  e.target.style.display = 'none'
}
</script>

<style lang="scss" scoped>
.training-page {
  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .training-progress {
    margin-bottom: 20px;
    
    .progress-info {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 14px;
      color: #606266;
    }
  }
  
  .training-output {
    margin: 20px 0;
    
    h4 {
      margin-bottom: 10px;
      color: #303133;
    }
    
    .output-container {
      background: #1e1e1e;
      border-radius: 4px;
      padding: 15px;
      max-height: 300px;
      overflow-y: auto;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 12px;
      
      .output-line {
        color: #d4d4d4;
        line-height: 1.6;
        white-space: pre-wrap;
        word-break: break-all;
      }
    }
  }
  
  .plots-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
    
    img {
      width: 100%;
      border-radius: 4px;
    }
  }
}
</style>
