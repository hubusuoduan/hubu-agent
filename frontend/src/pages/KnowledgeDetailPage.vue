<template>
  <div class="knowledge-detail-page">
    <div class="knowledge-detail-inner">
    <!-- 顶部返回栏 -->
    <div class="detail-header">
      <div class="back-btn" @click="goBack">
        <el-icon :size="16"><ArrowLeft /></el-icon>
        <span>返回知识库列表</span>
      </div>
    </div>

    <div v-loading="loading" class="detail-content">
      <!-- 知识库信息卡片 -->
      <div class="info-card">
        <div class="info-banner">
          <div class="banner-icon">
            <el-icon :size="32" color="#fff"><FolderOpened /></el-icon>
          </div>
          <div v-if="!editing" class="banner-text">
            <h2>{{ knowledge.name }}</h2>
            <p class="info-desc">{{ knowledge.description || '暂无描述' }}</p>
          </div>
          <div v-else class="banner-edit">
            <el-input v-model="editForm.name" placeholder="知识库名称" size="large" />
            <el-input
              v-model="editForm.description"
              type="textarea"
              :rows="2"
              placeholder="知识库描述"
            />
          </div>
          <div class="info-actions">
            <template v-if="!editing">
              <el-tooltip content="编辑信息" placement="top">
                <div class="action-btn edit-btn" @click="startEdit">
                  <el-icon :size="16"><Edit /></el-icon>
                </div>
              </el-tooltip>
              <el-tooltip content="删除知识库" placement="top">
                <div class="action-btn delete-btn" @click="handleDeleteKnowledge">
                  <el-icon :size="16"><Delete /></el-icon>
                </div>
              </el-tooltip>
            </template>
            <template v-else>
              <el-button size="small" @click="cancelEdit">取消</el-button>
              <el-button type="primary" size="small" @click="saveEdit" :loading="saving">保存</el-button>
            </template>
          </div>
        </div>
        <div class="info-stats">
          <div class="stat-item">
            <span class="stat-value">{{ files.length }}</span>
            <span class="stat-label">文件数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ totalSize }}</span>
            <span class="stat-label">总大小</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ successCount }}</span>
            <span class="stat-label">已索引</span>
          </div>
        </div>
      </div>

      <!-- 文件管理区域 -->
      <div class="files-section">
        <div class="files-toolbar">
          <div class="files-title">
            <el-icon :size="20" color="#6366f1"><Document /></el-icon>
            <span>文件列表</span>
            <span class="files-count">{{ files.length }}</span>
          </div>
          <el-upload
            :action="`/api/v1/knowledge/upload?knowledge_id=${knowledgeId}`"
            :headers="uploadHeaders"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :before-upload="beforeUpload"
            :show-file-list="false"
          >
            <el-button type="primary" size="small" plain>
              <el-icon><Upload /></el-icon>
              上传文件
            </el-button>
          </el-upload>
        </div>

        <div class="files-list" v-if="files.length > 0">
          <div v-for="file in files" :key="file.id" class="file-item">
            <div class="file-icon">
              <el-icon :size="22" :color="fileIconColor(file.file_name)"><Document /></el-icon>
            </div>
            <div class="file-info">
              <span class="file-name">{{ file.file_name }}</span>
              <div class="file-meta">
                <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
                <el-tag :type="statusTagType(file.status)" size="small" round>
                  {{ statusText(file.status) }}
                </el-tag>
              </div>
            </div>
            <el-button
              type="danger"
              size="small"
              text
              @click="handleDeleteFile(file)"
              class="file-delete-btn"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>

        <div v-else class="files-empty">
          <el-icon :size="48" color="#d1d5db"><Document /></el-icon>
          <p>暂无文件</p>
          <span>点击上方按钮上传文件到知识库</span>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, FolderOpened, Edit, Delete, Upload, Document } from '@element-plus/icons-vue'
import {
  getKnowledgeDetail,
  getKnowledgeFiles,
  deleteKnowledge,
  deleteKnowledgeFile,
  updateKnowledge,
  type Knowledge,
  type KnowledgeFile
} from '../apis/knowledge'

const route = useRoute()
const router = useRouter()
const knowledgeId = route.params.id as string

const loading = ref(false)
const saving = ref(false)
const editing = ref(false)
const knowledge = ref<Knowledge>({ id: '', name: '', description: '' })
const files = ref<KnowledgeFile[]>([])

const editForm = ref({ name: '', description: '' })

// 上传请求头
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`
}))

// 统计信息
const totalSize = computed(() => {
  const bytes = files.value.reduce((sum, f) => sum + f.file_size, 0)
  return formatFileSize(bytes)
})

const successCount = computed(() => {
  return files.value.filter(f => f.status === 'success').length
})

// 文件图标颜色
function fileIconColor(fileName: string): string {
  const ext = fileName.substring(fileName.lastIndexOf('.')).toLowerCase()
  const colorMap: Record<string, string> = {
    '.pdf': '#ef4444',
    '.docx': '#3b82f6',
    '.txt': '#6b7280',
    '.md': '#09b572',
    '.json': '#f59e0b',
    '.csv': '#8b5cf6'
  }
  return colorMap[ext] || '#6366f1'
}

// 加载知识库详情和文件列表
async function loadData() {
  loading.value = true
  try {
    const [detail, fileList] = await Promise.all([
      getKnowledgeDetail(knowledgeId),
      getKnowledgeFiles(knowledgeId)
    ])
    knowledge.value = detail
    files.value = fileList.items
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载失败')
    router.push('/knowledge')
  } finally {
    loading.value = false
  }
}

// 返回
function goBack() {
  router.push('/knowledge')
}

// 编辑
function startEdit() {
  editForm.value = {
    name: knowledge.value.name,
    description: knowledge.value.description || ''
  }
  editing.value = true
}

function cancelEdit() {
  editing.value = false
}

async function saveEdit() {
  if (!editForm.value.name.trim()) {
    ElMessage.warning('知识库名称不能为空')
    return
  }
  saving.value = true
  try {
    const updated = await updateKnowledge(knowledgeId, editForm.value)
    knowledge.value = updated
    editing.value = false
    ElMessage.success('更新成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    saving.value = false
  }
}

// 删除知识库
async function handleDeleteKnowledge() {
  try {
    await ElMessageBox.confirm('确定要删除该知识库吗？所有文件和知识将被清除，此操作不可恢复。', '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteKnowledge(knowledgeId)
    ElMessage.success('知识库已删除')
    router.push('/knowledge')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 删除文件
async function handleDeleteFile(file: KnowledgeFile) {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件「${file.file_name}」吗？该文件关联的知识数据也将被删除。`,
      '警告',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteKnowledgeFile(knowledgeId, file.id)
    ElMessage.success('文件已删除')
    await loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 上传前检查
function beforeUpload(file: File) {
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  const isValidType = ['.txt', '.pdf', '.docx', '.md', '.json', '.csv'].includes(ext)
  if (!isValidType) {
    ElMessage.error('只支持 .txt, .pdf, .docx, .md, .json, .csv 格式的文件')
    return false
  }
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  return true
}

// 上传成功
function handleUploadSuccess() {
  ElMessage.success('文件上传成功')
  loadData()
}

// 上传失败
function handleUploadError() {
  ElMessage.error('文件上传失败')
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 状态标签
function statusTagType(status: string): 'success' | 'warning' | 'danger' {
  if (status === 'success') return 'success'
  if (status === 'processing') return 'warning'
  return 'danger'
}

function statusText(status: string): string {
  if (status === 'success') return '已索引'
  if (status === 'processing') return '处理中'
  return '失败'
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
@import '../styles/knowledge-detail.css';
</style>
