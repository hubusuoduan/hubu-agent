
<template>
  <div class="workspace-page">
    <div class="workspace-page-inner">
      <!-- 顶部 Banner -->
      <div class="workspace-banner">
        <div class="banner-content">
          <div class="banner-info">
            <div class="banner-icon">
              <el-icon :size="28" color="#fff"><FolderOpened /></el-icon>
            </div>
            <div class="banner-text">
              <h2>工作区文件</h2>
              <p>管理 Agent 生成的文件，支持下载和删除</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 面包屑导航 -->
      <div class="workspace-breadcrumb" v-if="breadcrumbs.length > 0">
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

      <!-- 批量操作栏 -->
      <div class="workspace-toolbar">
        <div class="toolbar-left">
          <el-button
            v-if="!batchMode"
            type="default"
            @click="enterBatchMode"
          >
            <el-icon><Select /></el-icon>
            批量管理
          </el-button>
          <template v-else>
            <span class="batch-info">已选择 <b>{{ selectedRows.length }}</b> 项</span>
            <el-button
              type="primary"
              :disabled="selectedFileRows.length === 0"
              @click="handleBatchDownload"
            >
              <el-icon><Download /></el-icon>
              批量下载 ({{ selectedFileRows.length }})
            </el-button>
            <el-button
              type="danger"
              :disabled="selectedRows.length === 0"
              @click="handleBatchDelete"
            >
              <el-icon><Delete /></el-icon>
              批量删除
            </el-button>
            <el-button type="default" @click="exitBatchMode">退出批量</el-button>
          </template>
        </div>
      </div>

      <!-- 文件列表 -->
      <div class="workspace-table-wrapper" v-loading="loading">
        <el-table
          ref="tableRef"
          :data="fileList"
          style="width: 100%"
          :empty-text="'暂无文件'"
          @row-click="handleRowClick"
          :row-class-name="tableRowClassName"
          @selection-change="handleSelectionChange"
        >
          <el-table-column v-if="batchMode" type="selection" width="45" />
          <el-table-column label="文件名" min-width="300">
            <template #default="{ row }">
              <div class="file-name-cell">
                <el-icon :size="20" class="file-icon" :class="row.type === 'directory' ? 'icon-folder' : 'icon-file'">
                  <Folder v-if="row.type === 'directory'" />
                  <Document v-else />
                </el-icon>
                <span class="file-name">{{ row.name }}</span>
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
                :type="getFormatTagType(row.format)"
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
          <el-table-column v-if="!batchMode" label="操作" width="140" align="center" fixed="right">
            <template #default="{ row }">
              <div class="action-btns" @click.stop>
                <el-button
                  v-if="row.type === 'file'"
                  type="primary"
                  size="small"
                  text
                  @click="handleDownload(row)"
                >
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
                <el-button
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
      <div class="workspace-pagination" v-if="totalPages > 1">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Folder, FolderOpened, Document, Download, Delete, Select } from '@element-plus/icons-vue'
import type { ElTable } from 'element-plus'
import {
  getWorkspaceList,
  deleteWorkspaceFile,
  getWorkspaceDownloadUrl,
  type WorkspaceItem
} from '../apis/workspace'

const loading = ref(false)
const fileList = ref<WorkspaceItem[]>([])
const currentPath = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = ref(0)

// 批量管理
const batchMode = ref(false)
const selectedRows = ref<WorkspaceItem[]>([])
const tableRef = ref<InstanceType<typeof ElTable>>()

// 选中的文件行（排除目录，只有文件才能下载）
const selectedFileRows = computed(() => {
  return selectedRows.value.filter(row => row.type === 'file')
})

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

// 进入批量模式
function enterBatchMode() {
  batchMode.value = true
  selectedRows.value = []
}

// 退出批量模式
function exitBatchMode() {
  batchMode.value = false
  selectedRows.value = []
  nextTick(() => {
    tableRef.value?.clearSelection()
  })
}

// 表格选择变化
function handleSelectionChange(rows: WorkspaceItem[]) {
  selectedRows.value = rows
}

// 加载文件列表
async function loadFiles() {
  loading.value = true
  try {
    const res = await getWorkspaceList(currentPath.value, currentPage.value, pageSize.value)
    fileList.value = res.items
    total.value = res.total
    totalPages.value = res.total_pages
  } catch (error) {
    ElMessage.error('加载文件列表失败')
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

// 点击行：目录则进入（批量模式下不触发导航）
function handleRowClick(row: WorkspaceItem) {
  if (batchMode.value) return
  if (row.type === 'directory') {
    navigateTo(row.path)
  }
}

function tableRowClassName({ row }: { row: WorkspaceItem }) {
  return row.type === 'directory' ? 'row-directory' : 'row-file'
}

// 下载文件
function handleDownload(row: WorkspaceItem) {
  const url = getWorkspaceDownloadUrl(row.path)
  const link = document.createElement('a')
  link.href = url
  link.download = row.name
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 删除文件
async function handleDelete(row: WorkspaceItem) {
  const typeText = row.type === 'directory' ? '目录及其所有内容' : '文件'
  try {
    await ElMessageBox.confirm(
      `确定要删除${typeText} "${row.name}" 吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteWorkspaceFile(row.path)
    ElMessage.success('删除成功')
    loadFiles()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 批量下载
function handleBatchDownload() {
  const files = selectedFileRows.value
  if (files.length === 0) return

  files.forEach(row => {
    const url = getWorkspaceDownloadUrl(row.path)
    const link = document.createElement('a')
    link.href = url
    link.download = row.name
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  })

  ElMessage.success(`正在下载 ${files.length} 个文件`)
}

// 批量删除
async function handleBatchDelete() {
  if (selectedRows.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个项目吗？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const promises = selectedRows.value.map(row => deleteWorkspaceFile(row.path))
    const results = await Promise.allSettled(promises)

    const failedCount = results.filter(r => r.status === 'rejected').length
    if (failedCount > 0) {
      ElMessage.warning(`已删除 ${selectedRows.value.length - failedCount} 个，${failedCount} 个删除失败`)
    } else {
      ElMessage.success(`成功删除 ${selectedRows.value.length} 个项目`)
    }

    exitBatchMode()
    await loadFiles()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 分页
function handlePageChange(page: number) {
  currentPage.value = page
  loadFiles()
}

// 格式标签颜色
function getFormatTagType(format: string): string {
  const map: Record<string, string> = {
    pdf: 'danger',
    docx: 'primary',
    xlsx: 'success',
    pptx: 'warning',
    png: '', jpg: '', jpeg: '', gif: '', svg: '', webp: '',
    py: 'info', js: 'info', ts: 'info',
    md: '', txt: '', csv: 'success', json: 'info',
  }
  return map[format] || 'info'
}

onMounted(() => {
  loadFiles()
})
</script>

<style scoped>@import '../styles/workspace-page.css';</style>
