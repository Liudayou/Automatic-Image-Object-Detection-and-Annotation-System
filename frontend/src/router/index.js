import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/detection',
    name: 'Detection',
    component: () => import('@/views/Detection.vue'),
    meta: { title: '检测与标注' }
  },
  {
    path: '/batch',
    name: 'Batch',
    component: () => import('@/views/Batch.vue'),
    meta: { title: '批量处理' }
  },
  {
    path: '/training',
    name: 'Training',
    component: () => import('@/views/Training.vue'),
    meta: { title: '模型训练' }
  },
  {
    path: '/dataset',
    name: 'Dataset',
    component: () => import('@/views/Dataset.vue'),
    meta: { title: '数据集管理' }
  },
  {
    path: '/preprocessing',
    name: 'Preprocessing',
    component: () => import('@/views/Preprocessing.vue'),
    meta: { title: '数据预处理' }
  },
  {
    path: '/export',
    name: 'Export',
    component: () => import('@/views/Export.vue'),
    meta: { title: '导出管理' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
