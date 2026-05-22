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

.app-sidebar {
  width: 220px;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.sidebar-logo {
  padding: 24px 20px;
  font-size: 20px;
  font-weight: bold;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 12px;
}

.sidebar-nav {
  flex-shrink: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.8);
  font-size: 15px;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-item:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  color: white;
  background: rgba(255, 255, 255, 0.2);
  border-left: 4px solid white;
}

/* 对话历史列表样式 */
.sidebar-history {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: 8px;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 12px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.history-item.active {
  background: rgba(255, 255, 255, 0.15);
  color: white;
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
  color: rgba(255, 255, 255, 0.5) !important;
}

.history-item:hover .history-item-delete {
  opacity: 1;
}

.history-empty {
  text-align: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
}

.app-content {
  flex: 1;
  overflow: hidden;
  background-color: #f5f7fa;
}
</style>
