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
        <router-link to="/skills" class="nav-item" :class="{ active: route.path === '/skills' }">
          <el-icon><SetUp /></el-icon>
          <span>技能管理</span>
        </router-link>
        <router-link to="/workspace" class="nav-item" :class="{ active: route.path === '/workspace' }">
          <el-icon><Folder /></el-icon>
          <span>工作区文件</span>
        </router-link>
        <router-link to="/logs" class="nav-item" :class="{ active: route.path === '/logs' }">
          <el-icon><Notebook /></el-icon>
          <span>日志查看</span>
        </router-link>
        <router-link to="/dashboard" class="nav-item" :class="{ active: route.path === '/dashboard' }">
          <el-icon><DataAnalysis /></el-icon>
          <span>Token 统计</span>
        </router-link>
        <router-link to="/settings" class="nav-item" :class="{ active: route.path === '/settings' }">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </router-link>
      </div>
      <!-- 对话历史列表 -->
      <div class="sidebar-history">
        <div class="history-header">
          <span>历史对话</span>
        </div>
        <div class="history-list">
          <!-- 置顶对话 -->
          <template v-if="pinnedDialogs.length > 0">
            <div class="history-group-title">📌 置顶</div>
            <div
              v-for="dialog in pinnedDialogs"
              :key="dialog.dialog_id"
              :class="['history-item', { active: currentDialogId === dialog.dialog_id }]"
              @click="switchDialog(dialog)"
            >
              <el-icon class="history-item-icon icon-pinned"><Top /></el-icon>
              <span class="history-item-name">{{ dialog.name }}</span>
              <el-dropdown trigger="click" @command="(cmd: string) => handleDialogCommand(cmd, dialog.dialog_id)" @click.stop>
                <el-button class="history-item-more" size="small" text @click.stop>
                  <el-icon class="more-icon-rotated"><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="unpin" v-if="dialog.is_pinned">
                      <el-icon><Top /></el-icon> 取消置顶
                    </el-dropdown-item>
                    <el-dropdown-item command="pin" v-else>
                      <el-icon><Top /></el-icon> 置顶
                    </el-dropdown-item>
                    <el-dropdown-item command="unstar" v-if="dialog.is_starred">
                      <el-icon><Star /></el-icon> 取消收藏
                    </el-dropdown-item>
                    <el-dropdown-item command="star" v-else>
                      <el-icon><Star /></el-icon> 收藏
                    </el-dropdown-item>
                    <el-dropdown-item command="rename">
                      <el-icon><Edit /></el-icon> 重命名
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided class="dropdown-delete-item">
                      <el-icon><Delete /></el-icon> 删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>

          <!-- 收藏对话 -->
          <template v-if="starredDialogs.length > 0">
            <div class="history-group-title">⭐ 收藏</div>
            <div
              v-for="dialog in starredDialogs"
              :key="dialog.dialog_id"
              :class="['history-item', { active: currentDialogId === dialog.dialog_id }]"
              @click="switchDialog(dialog)"
            >
              <el-icon class="history-item-icon icon-starred"><Star /></el-icon>
              <span class="history-item-name">{{ dialog.name }}</span>
              <el-dropdown trigger="click" @command="(cmd: string) => handleDialogCommand(cmd, dialog.dialog_id)" @click.stop>
                <el-button class="history-item-more" size="small" text @click.stop>
                  <el-icon class="more-icon-rotated"><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="pin">
                      <el-icon><Top /></el-icon> 置顶
                    </el-dropdown-item>
                    <el-dropdown-item command="unstar">
                      <el-icon><Star /></el-icon> 取消收藏
                    </el-dropdown-item>
                    <el-dropdown-item command="rename">
                      <el-icon><Edit /></el-icon> 重命名
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided class="dropdown-delete-item">
                      <el-icon><Delete /></el-icon> 删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>

          <!-- 最近对话 -->
          <template v-if="recentDialogs.length > 0">
            <div class="history-group-title" v-if="pinnedDialogs.length > 0 || starredDialogs.length > 0">💬 最近</div>
            <div
              v-for="dialog in recentDialogs"
              :key="dialog.dialog_id"
              :class="['history-item', { active: currentDialogId === dialog.dialog_id }]"
              @click="switchDialog(dialog)"
            >
              <el-icon class="history-item-icon"><ChatDotRound /></el-icon>
              <span class="history-item-name">{{ dialog.name }}</span>
              <el-dropdown trigger="click" @command="(cmd: string) => handleDialogCommand(cmd, dialog.dialog_id)" @click.stop>
                <el-button class="history-item-more" size="small" text @click.stop>
                  <el-icon class="more-icon-rotated"><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="pin">
                      <el-icon><Top /></el-icon> 置顶
                    </el-dropdown-item>
                    <el-dropdown-item command="star">
                      <el-icon><Star /></el-icon> 收藏
                    </el-dropdown-item>
                    <el-dropdown-item command="rename">
                      <el-icon><Edit /></el-icon> 重命名
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided class="dropdown-delete-item">
                      <el-icon><Delete /></el-icon> 删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>

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
import { ChatDotRound, FolderOpened, Collection, SetUp, Setting, Refresh, Delete, DataAnalysis, Folder, Notebook, Top, Star, MoreFilled, Edit } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getDialogList, deleteDialog, pinDialog, starDialog, updateDialogName } from './apis/chat'
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

// 分组对话列表
const pinnedDialogs = computed(() => dialogList.value.filter(d => d.is_pinned))
const starredDialogs = computed(() => dialogList.value.filter(d => d.is_starred && !d.is_pinned))
const recentDialogs = computed(() => dialogList.value.filter(d => !d.is_pinned && !d.is_starred))

// 切换对话 - 通过路由跳转
const switchDialog = (dialog: DialogInfo) => {
  router.push(`/chat/${dialog.dialog_id}`)
}

// 下拉菜单命令分发
function handleDialogCommand(command: string, dialogId: string) {
  switch (command) {
    case 'pin': handlePinDialog(dialogId); break
    case 'unpin': handleUnpinDialog(dialogId); break
    case 'star': handleStarDialog(dialogId); break
    case 'unstar': handleUnstarDialog(dialogId); break
    case 'rename': handleRenameDialog(dialogId); break
    case 'delete': handleDeleteDialog(dialogId); break
  }
}

// 重命名对话
async function handleRenameDialog(dialogId: string) {
  const dialog = dialogList.value.find(d => d.dialog_id === dialogId)
  const oldName = dialog?.name || ''
  try {
    const { value } = await ElMessageBox.prompt('请输入新名称', '重命名对话', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: oldName,
      inputPattern: /^.{1,100}$/,
      inputErrorMessage: '名称长度为1-100个字符'
    })
    await updateDialogName(dialogId, value)
    ElMessage.success('重命名成功')
    refreshDialogs()
  } catch {
    // 用户取消
  }
}

// 置顶对话
async function handlePinDialog(dialogId: string) {
  try {
    await pinDialog(dialogId, true)
    ElMessage.success('已置顶')
    refreshDialogs()
  } catch (error) {
    ElMessage.error('置顶失败')
    console.error(error)
  }
}

// 取消置顶
async function handleUnpinDialog(dialogId: string) {
  try {
    await pinDialog(dialogId, false)
    ElMessage.success('已取消置顶')
    refreshDialogs()
  } catch (error) {
    ElMessage.error('取消置顶失败')
    console.error(error)
  }
}

// 收藏对话
async function handleStarDialog(dialogId: string) {
  try {
    await starDialog(dialogId, true)
    ElMessage.success('已收藏')
    refreshDialogs()
  } catch (error) {
    ElMessage.error('收藏失败')
    console.error(error)
  }
}

// 取消收藏
async function handleUnstarDialog(dialogId: string) {
  try {
    await starDialog(dialogId, false)
    ElMessage.success('已取消收藏')
    refreshDialogs()
  } catch (error) {
    ElMessage.error('取消收藏失败')
    console.error(error)
  }
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
@import './styles/global.css';
@import './styles/sidebar.css';
</style>
