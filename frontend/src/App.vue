<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <el-container>
        <!-- 侧边栏 -->
        <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">
          <div class="logo">
            <img src="@/assets/logo.svg" alt="logo" class="logo-img" />
            <span v-if="!isCollapse" class="logo-text">目标检测标注系统</span>
          </div>
          <el-menu
            :default-active="activeMenu"
            :collapse="isCollapse"
            :router="true"
            class="app-menu"
            background-color="#304156"
            text-color="#bfcbd9"
            active-text-color="#409EFF"
          >
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/detection">
              <el-icon><Camera /></el-icon>
              <span>检测与标注</span>
            </el-menu-item>
            <el-menu-item index="/batch">
              <el-icon><Files /></el-icon>
              <span>批量处理</span>
            </el-menu-item>
            <el-menu-item index="/training">
              <el-icon><DataLine /></el-icon>
              <span>模型训练</span>
            </el-menu-item>
            <el-menu-item index="/dataset">
              <el-icon><FolderOpened /></el-icon>
              <span>数据集管理</span>
            </el-menu-item>
            <el-menu-item index="/preprocessing">
              <el-icon><MagicStick /></el-icon>
              <span>数据预处理</span>
            </el-menu-item>
            <el-menu-item index="/export">
              <el-icon><Download /></el-icon>
              <span>导出管理</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <el-container>
          <!-- 头部 -->
          <el-header class="app-header">
            <div class="header-left">
              <el-button 
                :icon="isCollapse ? 'Expand' : 'Fold'" 
                @click="isCollapse = !isCollapse"
                text
              />
              <el-breadcrumb separator="/">
                <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
                <el-breadcrumb-item v-if="currentRoute.meta?.title">
                  {{ currentRoute.meta.title }}
                </el-breadcrumb-item>
              </el-breadcrumb>
            </div>
            <div class="header-right">
              <el-tooltip content="系统信息">
                <el-button :icon="InfoFilled" circle @click="showSystemInfo" />
              </el-tooltip>
              <el-tooltip content="GitHub">
                <el-button :icon="Link" circle @click="openGithub" />
              </el-tooltip>
            </div>
          </el-header>

          <!-- 主内容区 -->
          <el-main class="app-main">
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </el-main>
        </el-container>
      </el-container>

      <!-- 系统信息对话框 -->
      <el-dialog v-model="systemInfoVisible" title="系统信息" width="400px">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="应用名称">{{ systemInfo.app_name }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ systemInfo.version }}</el-descriptions-item>
          <el-descriptions-item label="CUDA可用">
            <el-tag :type="systemInfo.cuda_available ? 'success' : 'danger'">
              {{ systemInfo.cuda_available ? '是' : '否' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="GPU设备" v-if="systemInfo.cuda_device_name">
            {{ systemInfo.cuda_device_name }}
          </el-descriptions-item>
        </el-descriptions>
      </el-dialog>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { InfoFilled, Link } from '@element-plus/icons-vue'
import api from '@/api'

const route = useRoute()
const isCollapse = ref(false)
const systemInfoVisible = ref(false)
const systemInfo = ref({})

const activeMenu = computed(() => route.path)
const currentRoute = computed(() => route)

const showSystemInfo = async () => {
  try {
    const res = await api.getSystemInfo()
    systemInfo.value = res.data
    systemInfoVisible.value = true
  } catch (error) {
    console.error('获取系统信息失败:', error)
  }
}

const openGithub = () => {
  window.open('https://github.com/ultralytics/yolov5', '_blank')
}

onMounted(() => {
  // 预加载系统信息
  api.getSystemInfo().then(res => {
    systemInfo.value = res.data
  }).catch(() => {})
})
</script>

<style lang="scss" scoped>
.app-container {
  height: 100vh;
  
  .el-container {
    height: 100%;
  }
}

.app-aside {
  background-color: #304156;
  transition: width 0.3s;
  overflow: hidden;
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 15px;
    background-color: #263445;
    
    .logo-img {
      width: 32px;
      height: 32px;
    }
    
    .logo-text {
      margin-left: 10px;
      color: #fff;
      font-size: 14px;
      font-weight: bold;
      white-space: nowrap;
    }
  }
  
  .app-menu {
    border-right: none;
    
    &:not(.el-menu--collapse) {
      width: 220px;
    }
  }
}

.app-header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 15px;
  }
  
  .header-right {
    display: flex;
    gap: 10px;
  }
}

.app-main {
  background-color: #f0f2f5;
  padding: 20px;
  overflow: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
