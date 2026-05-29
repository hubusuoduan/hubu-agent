<template>
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
          @click="$emit('switch', dialog)"
        >
          <el-icon class="history-item-icon icon-pinned"><Top /></el-icon>
          <span class="history-item-name">{{ dialog.name }}</span>
          <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, dialog)" @click.stop>
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
          @click="$emit('switch', dialog)"
        >
          <el-icon class="history-item-icon icon-starred"><Star /></el-icon>
          <span class="history-item-name">{{ dialog.name }}</span>
          <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, dialog)" @click.stop>
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
          @click="$emit('switch', dialog)"
        >
          <el-icon class="history-item-icon"><ChatDotRound /></el-icon>
          <span class="history-item-name">{{ dialog.name }}</span>
          <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, dialog)" @click.stop>
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
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { ChatDotRound, Top, Star, MoreFilled, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getDialogList, deleteDialog, pinDialog, starDialog, updateDialogName } from '../apis/chat'
import type { DialogInfo } from '../apis/chat'

const props = defineProps<{
  currentDialogId: string | null
}>()

const emit = defineEmits<{
  switch: [dialog: DialogInfo]
  delete: [dialogId: string]
}>()

// 对话列表数据
const dialogList = ref<DialogInfo[]>([])

// 分组
const pinnedDialogs = computed(() => dialogList.value.filter(d => d.is_pinned))
const starredDialogs = computed(() => dialogList.value.filter(d => d.is_starred && !d.is_pinned))
const recentDialogs = computed(() => dialogList.value.filter(d => !d.is_pinned && !d.is_starred))

// 加载对话列表
const refreshDialogs = async () => {
  try {
    const result = await getDialogList()
    dialogList.value = result.dialogs || []
  } catch (error) {
    console.error('加载对话列表失败:', error)
  }
}

// 下拉菜单命令分发
function handleCommand(command: string, dialog: DialogInfo) {
  const dialogId = dialog.dialog_id
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
async function handleDeleteDialog(dialogId: string) {
  try {
    await ElMessageBox.confirm('确定要删除该对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteDialog(dialogId)
    ElMessage.success('对话已删除')
    emit('delete', dialogId)
    refreshDialogs()
  } catch {
    // 用户取消
  }
}

// 监听全局刷新事件
function _onRefreshDialogs() {
  refreshDialogs()
}

onMounted(() => {
  refreshDialogs()
  window.addEventListener('refresh-dialogs', _onRefreshDialogs)
})

onBeforeUnmount(() => {
  window.removeEventListener('refresh-dialogs', _onRefreshDialogs)
})

// 暴露刷新方法供父组件调用
defineExpose({ refreshDialogs })
</script>

<style scoped>
/* 对话历史列表 */
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

/* 分组标题 */
.history-group-title {
  padding: 10px 12px 4px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  user-select: none;
}

/* 三点菜单 */
.more-icon-rotated {
  transform: rotate(90deg);
}

.history-item-more {
  opacity: 0;
  transition: opacity 0.2s, color 0.2s;
  color: rgba(255, 255, 255, 0.35) !important;
  padding: 4px !important;
  margin: 0 !important;
  flex-shrink: 0;
  background: transparent !important;
}

.history-item:hover .history-item-more {
  opacity: 1;
}

.history-item-more:hover {
  color: #22c55e !important;
  background: transparent !important;
}

.history-item-more:focus {
  background: transparent !important;
}

.history-item-more:active {
  background: transparent !important;
}

/* 置顶图标颜色 */
.icon-pinned {
  color: #f59e0b !important;
}

/* 收藏图标颜色 */
.icon-starred {
  color: #fbbf24 !important;
}

/* 下拉菜单删除项 hover 变红 */
.dropdown-delete-item {
  color: #ef4444 !important;
}

:deep(.el-dropdown-menu__item.dropdown-delete-item:hover) {
  background-color: #fef2f2 !important;
  color: #ef4444 !important;
}

.history-empty {
  text-align: center;
  padding: 24px;
  color: rgba(255, 255, 255, 0.25);
  font-size: 13px;
}
</style>
