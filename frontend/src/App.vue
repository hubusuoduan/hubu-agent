<template>
  <div id="app">
    <nav v-if="showSidebar" class="app-sidebar">
      <div class="sidebar-logo">Hubu Agent</div>
      <div class="sidebar-nav">
        <router-link to="/chat" class="nav-item" :class="{ active: route.path === '/chat' }">
          <el-icon><ChatDotRound /></el-icon>
          <span>新对话</span>
        </router-link>
        <router-link to="/knowledge" class="nav-item" :class="{ active: route.path.startsWith('/knowledge') }">
          <el-icon><FolderOpened /></el-icon>
          <span>知识库</span>
        </router-link>
        <router-link to="/memory" class="nav-item" :class="{ active: route.path === '/memory' }">
          <el-icon><Collection /></el-icon>
          <span>记忆管理</span>
        </router-link>
        <router-link to="/user-agent" class="nav-item" :class="{ active: route.path === '/user-agent' }">
          <el-icon><MagicStick /></el-icon>
          <span>自定义Agent</span>
        </router-link>
        <router-link to="/skills" class="nav-item" :class="{ active: route.path === '/skills' }">
          <el-icon><SetUp /></el-icon>
          <span>技能管理</span>
        </router-link>
        <router-link to="/provider" class="nav-item" :class="{ active: route.path === '/provider' }">
          <el-icon><Cpu /></el-icon>
          <span>模型配置</span>
        </router-link>
        <router-link to="/workspace" class="nav-item" :class="{ active: route.path === '/workspace' }">
          <el-icon><Folder /></el-icon>
          <span>工作区文件</span>
        </router-link>
        <router-link v-if="isAdmin" to="/logs" class="nav-item" :class="{ active: route.path === '/logs' }">
          <el-icon><Notebook /></el-icon>
          <span>日志查看</span>
        </router-link>
        <router-link to="/dashboard" class="nav-item" :class="{ active: route.path === '/dashboard' }">
          <el-icon><DataAnalysis /></el-icon>
          <span>Token 统计</span>
        </router-link>
        <router-link to="/profile" class="nav-item" :class="{ active: route.path === '/profile' }">
          <el-icon><User /></el-icon>
          <span>个人信息</span>
        </router-link>
        <router-link to="/settings" class="nav-item" :class="{ active: route.path === '/settings' }">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </router-link>
      </div>
      <!-- 对话历史列表 -->
      <DialogHistoryList
        :current-dialog-id="currentDialogId"
        @switch="switchDialog"
        @delete="handleDialogDeleted"
      />
    </nav>
    <div class="app-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotRound, FolderOpened, Collection, SetUp, Setting, DataAnalysis, Folder, Notebook, User, MagicStick, Cpu } from '@element-plus/icons-vue'
import DialogHistoryList from './components/DialogHistoryList.vue'

const route = useRoute()
const router = useRouter()

const showSidebar = computed(() => {
  return route.meta.requiresAuth !== false
})

// 是否为管理员 - 响应式
const userRole = ref(localStorage.getItem('user_role') || '0')
// 监听 localStorage 变化（其他标签页或同页面修改）
window.addEventListener('storage', (e) => {
  if (e.key === 'user_role') {
    userRole.value = e.newValue || '0'
  }
})
// 暴露一个全局方法让登录页可以通知角色变化
;(window as any).__updateUserRole = (role: string) => {
  userRole.value = role
}
const isAdmin = computed(() => userRole.value === '1')

// 当前对话ID，从路由参数获取
const currentDialogId = computed(() => {
  return (route.params.dialogId as string) || null
})

// 切换对话 - 通过路由跳转
const switchDialog = (dialog: { dialog_id: string }) => {
  router.push(`/chat/${dialog.dialog_id}`)
}

// 对话被删除时的处理
const handleDialogDeleted = (dialogId: string) => {
  if (currentDialogId.value === dialogId) {
    router.push('/chat')
  }
}
</script>

<style>
@import './styles/global.css';
@import './styles/sidebar.css';
</style>
