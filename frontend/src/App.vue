<template>
  <div id="app">
    <nav v-if="showSidebar" class="app-sidebar">
      <div class="sidebar-logo">Hubu Agent</div>
      <div class="sidebar-nav">
        <router-link to="/chat" class="nav-item" :class="{ active: route.path === '/chat' }">
          <el-icon><ChatDotRound /></el-icon>
          <span>新对话</span>
        </router-link>
        <router-link to="/knowledge" class="nav-item" active-class="active">
          <el-icon><FolderOpened /></el-icon>
          <span>知识库</span>
        </router-link>
        <router-link to="/memory" class="nav-item" active-class="active">
          <el-icon><Collection /></el-icon>
          <span>记忆管理</span>
        </router-link>
      </div>
      <!-- 对话历史列表 -->
      <div class="sidebar-history">
        <div class="history-header">
          <span>历史对话</span>
          <el-button size="small" text @click="refreshDialogs" :loading="loadingDialogs">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        <div class="history-list">
          <div
            v-for="dialog in dialogList"
            :key="dialog.dialog_id"
            :class="['history-item', { active: currentDialogId === dialog.dialog_id }]"
            @click="switchDialog(dialog)"
          >
            <el-icon class="history-item-icon"><ChatDotRound /></el-icon>
            <span class="history-item-name">{{ dialog.name }}</span>
            <el-button
              class="history-item-delete"
              size="small"
              text
              @click.stop="handleDeleteDialog(dialog.dialog_id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <div v-if="dialogList.length === 0" class="history-empty">
            暂无历史对话
          </div>
        </div>
      </div>
    </nav>
    <div class="app-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotRound, FolderOpened, Collection, Refresh, Delete } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getDialogList, deleteDialog } from './apis/chat'
import type { DialogInfo } from './apis/chat'

const route = useRoute()
const router = useRouter()

const showSidebar = computed(() => {
  return route.meta.requiresAuth !== false
})

// 当前对话ID，从路由参数获取
const currentDialogId = computed(() => {
  return (route.params.dialogId as string) || null
})

// 对话列表相关
const dialogList = ref<DialogInfo[]>([])
const loadingDialogs = ref(false)

// 加载对话列表
const refreshDialogs = async () => {
  if (!showSidebar.value) return
  loadingDialogs.value = true
  try {
    const result = await getDialogList()
    dialogList.value = result.dialogs || []
  } catch (error) {
    console.error('加载对话列表失败:', error)
  } finally {
    loadingDialogs.value = false
  }
}

// 切换对话 - 通过路由跳转
const switchDialog = (dialog: DialogInfo) => {
  router.push(`/chat/${dialog.dialog_id}`)
}

// 删除对话
const handleDeleteDialog = async (dialogId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除该对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteDialog(dialogId)
    ElMessage.success('对话已删除')
    // 如果删除的是当前对话，跳转到新对话页面
    if (currentDialogId.value === dialogId) {
      router.push('/chat')
    }
    refreshDialogs()
  } catch {
    // 用户取消
  }
}

// 监听新建对话事件，刷新列表
onMounted(() => {
  refreshDialogs()
  window.addEventListener('refresh-dialogs', () => {
    refreshDialogs()
  })
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  height: 100vh;
  width: 100vw;
  display: flex;
}

/* 全局覆盖 Element Plus 主色为绿色 */
:root {
  --el-color-primary: #09b572;
  --el-color-primary-light-3: #3cc88f;
  --el-color-primary-light-5: #6ddaaa;
  --el-color-primary-light-7: #9eedc5;
  --el-color-primary-light-8: #b5f2d4;
  --el-color-primary-light-9: #ccf7e3;
  --el-color-primary-dark-2: #07925b;
}

.el-button--primary {
  --el-button-bg-color: #09b572;
  --el-button-border-color: #09b572;
  --el-button-hover-bg-color: #07a065;
  --el-button-hover-border-color: #07a065;
  --el-button-active-bg-color: #07925b;
  --el-button-active-border-color: #07925b;
}

.el-button--primary.is-plain {
  --el-button-bg-color: #ecfaf3;
  --el-button-border-color: #3cc88f;
  --el-button-hover-bg-color: #09b572;
  --el-button-hover-border-color: #09b572;
  --el-button-hover-text-color: #ffffff;
}

.el-button--primary.is-text {
  --el-button-hover-bg-color: rgba(9, 181, 114, 0.1);
  --el-button-hover-text-color: #09b572;
}

.app-sidebar {
  width: 240px;
  background: #2c2c2c;
  color: white;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.15);
}

.sidebar-logo {
  padding: 28px 20px;
  font-size: 18px;
  font-weight: 700;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 8px;
  letter-spacing: 1px;
  color: #09b572;
}

.sidebar-nav {
  flex-shrink: 0;
  padding: 4px 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.55);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  margin-bottom: 2px;
}

.nav-item:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.06);
}

.nav-item.active {
  color: white;
  background: rgba(9, 181, 114, 0.15);
  border-left: none;
  box-shadow: inset 0 0 0 1px rgba(9, 181, 114, 0.25);
}

.nav-item.active .el-icon {
  color: #09b572;
}

/* 对话历史列表样式 */
.sidebar-history {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  margin-top: 8px;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 12px;
}

.history-list::-webkit-scrollbar {
  width: 4px;
}

.history-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.85);
}

.history-item.active {
  background: rgba(9, 181, 114, 0.12);
  color: rgba(255, 255, 255, 0.95);
}

.history-item-icon {
  flex-shrink: 0;
  font-size: 14px;
}

.history-item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-item-delete {
  opacity: 0;
  transition: opacity 0.2s;
  color: rgba(255, 255, 255, 0.35) !important;
}

.history-item:hover .history-item-delete {
  opacity: 1;
}

.history-empty {
  text-align: center;
  padding: 24px;
  color: rgba(255, 255, 255, 0.25);
  font-size: 13px;
}

.app-content {
  flex: 1;
  overflow: hidden;
  background-color: #f5f5f5;
}
</style>
