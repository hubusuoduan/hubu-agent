
<template>
  <div class="logs-page">
    <div class="logs-page-inner">
      <!-- 顶部 Banner -->
      <div class="logs-banner">
        <div class="banner-content">
          <div class="banner-info">
            <div class="banner-icon">
              <el-icon :size="28" color="#fff"><Notebook /></el-icon>
            </div>
            <div class="banner-text">
              <h2>日志查看</h2>
              <p>浏览后端日志文件，点击 .log 文件查看内容</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 面包屑导航 -->
      <div class="logs-breadcrumb" v-if="breadcrumbs.length > 0">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item @click="navigateTo('')">
            <span class="breadcrumb-link">根目录</span>
          </el-breadcrumb-item>
          <el-breadcrumb-item
            v-for="(crumb, index) in breadcrumbs"
            :key="index"
            @click="navigateTo(crumb.path)"
          >
            <span class="breadcrumb-link">{{ crumb.name }}</span>
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>

      <!-- 文件列表 -->
      <div class="logs-table-wrapper" v-loading="loading">
        <el-table
          :data="fileList"
          style="width: 100%"
          :empty-text="'暂无日志文件'"
          @row-click="handleRowClick"
          :row-class-name="tableRowClassName"
        >
          <el-table-column label="文件名" min-width="300">
            <template #default="{ row }">
              <div class="file-name-cell">
                <el-icon :size="20" class="file-icon" :class="row.type === 'directory' ? 'icon-folder' : (isLogFile(row) ? 'icon-log' : 'icon-file')">
                  <Folder v-if="row.type === 'directory'" />
                  <Document v-else-if="!isLogFile(row)" />
                  <Notebook v-else />
                </el-icon>
                <span class="file-name" :class="{ 'log-file-name': isLogFile(row) }">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="大小" width="120" align="right">
            <template #default="{ row }">
              <span v-if="row.type === 'file'" class="file-size">{{ row.size_text }}</span>
              <span v-else class="file-size">-</span>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                v-if="row.type === 'file' && row.format"
                size="small"
                :type="row.format === 'log' ? 'warning' : 'info'"
                effect="plain"
              >
                {{ row.format.toUpperCase() }}
              </el-tag>
              <el-tag v-else-if="row.type === 'directory'" size="small" type="info" effect="plain">
                文件夹
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="修改时间" width="160" align="center">
            <template #default="{ row }">
              <span class="file-time">{{ row.modify_time || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" align="center" fixed="right">
            <template #default="{ row }">
              <div class="action-btns" @click.stop>
                <el-button
                  v-if="isLogFile(row)"
                  type="primary"
                  size="small"
                  text
                  @click="handleView(row)"
                >
                  <el-icon><View /></el-icon>
                  查看
                </el-button>
                <el-button
                  v-if="row.type === 'file'"
                  type="danger"
                  size="small"
                  text
                  @click="handleDelete(row)"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="logs-pagination" v-if="totalPages > 1">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 日志内容查看弹窗 -->
    <el-dialog
      v-model="logDialogVisible"
      :title="logFileName"
      width="80%"
      top="5vh"
      destroy-on-close
      class="log-viewer-dialog"
    >
      <div class="log-viewer-header">
        <div class="log-viewer-info">
          <el-tag size="small" type="info">共 {{ logTotalLines }} 行</el-tag>
          <el-tag size="small" type="warning">显示最后 {{ logShowingLines }} 行</el-tag>
        </div>
        <div class="log-viewer-actions">
          <el-input-number
            v-model="tailLines"
            :min="100"
            :max="5000"
            :step="100"
            size="small"
            style="width: 140px"
          />
          <el-button size="small" @click="reloadLogContent" :loading="logContentLoading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button size="small" @click="toggleAutoRefresh">
            <el-icon><Timer /></el-icon>
            {{ autoRefresh ? '停止自动' : '自动刷新' }}
          </el-button>
        </div>
      </div>
      <div class="log-viewer-content" v-loading="logContentLoading">
        <pre><code>{{ logContent }}</code></pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Folder, Document, Notebook, View, Delete, Refresh, Timer } from '@element-plus/icons-vue'
import {
  getLogList,
  readLogFile,
  deleteLogFile,
  type LogItem
} from '../apis/logs'

const loading = ref(false)
const fileList = ref<LogItem[]>([])
const currentPath = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = ref(0)

// 面包屑
const breadcrumbs = computed(() => {
  if (!currentPath.value) return []
  const parts = currentPath.value.split('/')
  const result: { name: string; path: string }[] = []
  let pathAccum = ''
  for (const part of parts) {
    pathAccum = pathAccum ? `${pathAccum}/${part}` : part
    result.push({ name: part, path: pathAccum })
  }
  return result
})

// 判断是否为 .log 文件
function isLogFile(row: LogItem): boolean {
  return row.type === 'file' && row.format === 'log'
}

// 加载文件列表
async function loadFiles() {
  loading.value = true
  try {
    const res = await getLogList(currentPath.value, currentPage.value, pageSize.value)
    fileList.value = res.items
    total.value = res.total
    totalPages.value = res.total_pages
  } catch (error) {
    ElMessage.error('加载日志列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 导航到指定目录
function navigateTo(path: string) {
  currentPath.value = path
  currentPage.value = 1
  loadFiles()
}

// 点击行：目录则进入，.log 文件则查看
function handleRowClick(row: LogItem) {
  if (row.type === 'directory') {
    navigateTo(row.path)
  } else if (isLogFile(row)) {
    handleView(row)
  }
}

function tableRowClassName({ row }: { row: LogItem }) {
  if (row.type === 'directory') return 'row-directory'
  if (isLogFile(row)) return 'row-log-file'
  return 'row-file'
}

// ========== 日志内容查看 ==========
const logDialogVisible = ref(false)
const logContent = ref('')
const logFileName = ref('')
const logFilePath = ref('')
const logTotalLines = ref(0)
const logShowingLines = ref(0)
const tailLines = ref(500)
const logContentLoading = ref(false)
const autoRefresh = ref(false)
let autoRefreshTimer: ReturnType<typeof setInterval> | null = null

async function handleView(row: LogItem) {
  logFileName.value = row.name
  logFilePath.value = row.path
  logDialogVisible.value = true
  await loadLogContent()
}

async function loadLogContent() {
  if (!logFilePath.value) return
  logContentLoading.value = true
  try {
    const res = await readLogFile(logFilePath.value, tailLines.value)
    logContent.value = res.content
    logTotalLines.value = res.total_lines
    logShowingLines.value = res.showing_lines
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '读取日志失败')
    console.error(error)
  } finally {
    logContentLoading.value = false
  }
}

async function reloadLogContent() {
  await loadLogContent()
}

function toggleAutoRefresh() {
  if (autoRefresh.value) {
    // 停止
    if (autoRefreshTimer) {
      clearInterval(autoRefreshTimer)
      autoRefreshTimer = null
    }
    autoRefresh.value = false
  } else {
    // 开始自动刷新，每 3 秒
    autoRefresh.value = true
    autoRefreshTimer = setInterval(() => {
      loadLogContent()
    }, 3000)
  }
}

// 删除日志文件
async function handleDelete(row: LogItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除日志文件 "${row.name}" 吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteLogFile(row.path)
    ElMessage.success('删除成功')
    loadFiles()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 分页
function handlePageChange(page: number) {
  currentPage.value = page
  loadFiles()
}

onMounted(() => {
  loadFiles()
})

onUnmounted(() => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
  }
})
</script>

<style scoped>@import '../styles/logs-page.css';</style>
