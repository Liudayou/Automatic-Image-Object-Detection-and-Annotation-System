import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 60000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response
  },
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// API 方法
const api = {
  // 系统
  getSystemInfo: () => request.get('/system/info'),
  healthCheck: () => request.get('/health'),
  
  // 检测
  detect: (formData, config = {}) => request.post('/detection/detect', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...config
  }),
  detectBatch: (formData) => request.post('/detection/detect/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getWeights: () => request.get('/detection/weights'),
  getClasses: () => request.get('/detection/classes'),
  getModelInfo: (weights) => request.get('/detection/model/info', { params: { weights } }),
  
  // 标注
  saveAnnotations: (data) => request.post('/annotation/save', data),
  getAnnotations: (imageId) => request.get(`/annotation/${imageId}`),
  deleteAnnotations: (imageId) => request.delete(`/annotation/${imageId}`),
  listAnnotations: (page = 1, pageSize = 20) => request.get('/annotation/', { 
    params: { page, page_size: pageSize } 
  }),
  updateAnnotation: (imageId, annotationId, data) => 
    request.put(`/annotation/${imageId}/annotation/${annotationId}`, data),
  deleteAnnotation: (imageId, annotationId) => 
    request.delete(`/annotation/${imageId}/annotation/${annotationId}`),
  addAnnotation: (imageId, data) => 
    request.post(`/annotation/${imageId}/annotation`, data),
  
  // 导出
  exportAnnotations: (data) => request.post('/export/', data),
  downloadExport: (data) => request.post('/export/download', data, { responseType: 'blob' }),
  getExportFormats: () => request.get('/export/formats'),
  
  // 训练
  startTraining: (config) => request.post('/training/start', config),
  getTrainingStatus: (taskId) => request.get(`/training/status/${taskId}`),
  getTrainingOutput: (taskId) => request.get(`/training/output/${taskId}`),
  stopTraining: (taskId) => request.post(`/training/stop/${taskId}`),
  listTrainingTasks: () => request.get('/training/list'),
  getTrainingResults: (taskId) => request.get(`/training/results/${taskId}`),
  getDatasets: () => request.get('/training/datasets'),
  getHyperparameters: () => request.get('/training/hyperparameters'),
  
  // 数据集
  listDatasets: () => request.get('/dataset/list'),
  getDatasetInfo: (name) => request.get(`/dataset/${name}`),
  createDataset: (formData) => request.post('/dataset/create', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  uploadDatasetImages: (name, formData, split = 'train') => 
    request.post(`/dataset/${name}/upload?split=${split}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  deleteDataset: (name) => request.delete(`/dataset/${name}`),
  listDatasetImages: (name, split = 'train', page = 1, pageSize = 20) =>
    request.get(`/dataset/${name}/images`, { params: { split, page, page_size: pageSize } }),
  
  // 预处理
  augmentImage: (formData) => request.post('/preprocessing/augment', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  batchAugment: (formData) => request.post('/preprocessing/batch-augment', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  checkQuality: (formData) => request.post('/preprocessing/quality-check', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  batchQualityCheck: (formData) => request.post('/preprocessing/batch-quality-check', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export default api
