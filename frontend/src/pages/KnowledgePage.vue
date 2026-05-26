<template>
  <div class="knowledge-page">
    <div class="knowledge-page-inner">
    <!-- 顶部 Banner -->
    <div class="knowledge-banner">
      <div class="banner-content">
        <div class="banner-info">
          <div class="banner-icon">
            <el-icon :size="28" color="#fff"><FolderOpened /></el-icon>
          </div>
          <div class="banner-text">
            <h2>知识库管理</h2>
            <p>创建和管理知识库，为 AI 对话提供专业知识支撑</p>
          </div>
        </div>
        <el-button type="primary" size="large" round @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建知识库
        </el-button>
      </div>
      <!-- 统计信息 -->
      <div class="banner-stats">
        <div class="stat-item">
          <span class="stat-value">{{ knowledgeList.length }}</span>
          <span class="stat-label">知识库总数</span>
        </div>
      </div>
    </div>

    <!-- 搜索与操作栏 -->
    <div class="knowledge-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索知识库名称或描述..."
          clearable
          :prefix-icon="Search"
          class="search-input"
        />
        <el-button
          v-if="!batchMode"
          type="default"
          @click="enterBatchMode"
        >
          <el-icon><Select /></el-icon>
          批量管理
        </el-button>
        <template v-else>
          <el-button type="default" @click="toggleSelectAll">
            {{ isAllSelected ? '取消全选' : '全选' }}
          </el-button>
          <el-button
            type="danger"
            :disabled="selectedIds.length === 0"
            @click="handleBatchDelete"
          >
            <el-icon><Delete /></el-icon>
            删除选中 ({{ selectedIds.length }})
          </el-button>
          <el-button type="default" @click="exitBatchMode">退出批量</el-button>
        </template>
      </div>
    </div>

    <!-- 知识库列表 -->
    <div class="knowledge-list">
      <div
        v-for="kb in filteredList"
        :key="kb.id"
        class="knowledge-card"
        :class="{ 'card-selected': selectedIds.includes(kb.id), 'card-selectable': batchMode }"
        @click="handleCardClick(kb)"
      >
        <div class="card-color-bar"></div>
        <div class="card-body">
          <div class="card-header">
            <div v-if="batchMode" class="card-checkbox" @click.stop="toggleSelect(kb.id)">
              <el-checkbox :model-value="selectedIds.includes(kb.id)" />
            </div>
            <div class="card-icon">
              <el-icon :size="20" color="#e28407"><FolderOpened /></el-icon>
            </div>
            <div class="card-title-area">
              <h3>{{ kb.name }}</h3>
              <p class="card-description">{{ kb.description || '暂无描述' }}</p>
            </div>
          </div>
          <div class="card-footer">
            <div class="card-meta">
              <span class="meta-item">
                <el-icon :size="12"><Document /></el-icon>
                知识库
              </span>
            </div>
            <div class="card-actions" v-if="!batchMode">
              <div class="action-icon-btn danger" @click.stop="handleDelete(kb.id)">
                <el-icon :size="14"><Delete /></el-icon>
              </div>
              <div class="enter-link">
                <span>查看详情</span>
                <el-icon :size="12"><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="filteredList.length === 0 && knowledgeList.length > 0" class="empty-state">
        <div class="empty-icon">🔍</div>
        <p class="empty-title">未找到匹配的知识库</p>
        <p class="empty-desc">尝试使用其他关键词搜索</p>
      </div>

      <div v-if="knowledgeList.length === 0" class="empty-state">
        <div class="empty-icon">📚</div>
        <p class="empty-title">暂无知识库</p>
        <p class="empty-desc">点击上方按钮创建你的第一个知识库</p>
      </div>
    </div>

    <!-- 创建知识库对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建知识库"
      width="500px"
    >
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入知识库描述（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, FolderOpened, ArrowRight, Document, Search, Select } from '@element-plus/icons-vue'
import {
  createKnowledge,
  getKnowledgeList,
  deleteKnowledge,
  type Knowledge
} from '../apis/knowledge'

const router = useRouter()
const knowledgeList = ref<Knowledge[]>([])
const showCreateDialog = ref(false)
const creating = ref(false)
const searchKeyword = ref('')
const batchMode = ref(false)
const selectedIds = ref<string[]>([])

const createForm = ref({
  name: '',
  description: ''
})

// 模糊搜索过滤
const filteredList = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return knowledgeList.value
  return knowledgeList.value.filter(kb =>
    kb.name.toLowerCase().includes(keyword) ||
    (kb.description && kb.description.toLowerCase().includes(keyword))
  )
})

// 是否全选
const isAllSelected = computed(() => {
  return filteredList.value.length > 0 && filteredList.value.every(kb => selectedIds.value.includes(kb.id))
})

// 进入批量模式
function enterBatchMode() {
  batchMode.value = true
  selectedIds.value = []
}

// 退出批量模式
function exitBatchMode() {
  batchMode.value = false
  selectedIds.value = []
}

// 切换选中
function toggleSelect(id: string) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1)
  } else {
    selectedIds.value.push(id)
  }
}

// 全选/取消全选
function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = filteredList.value.map(kb => kb.id)
  }
}

// 卡片点击：批量模式下切换选中，否则进入详情
function handleCardClick(kb: Knowledge) {
  if (batchMode.value) {
    toggleSelect(kb.id)
  } else {
    goToDetail(kb.id)
  }
}

// 进入知识库详情
function goToDetail(id: string) {
  router.push(`/knowledge/${id}`)
}

// 加载知识库列表
async function loadKnowledgeList() {
  try {
    const response = await getKnowledgeList(0, 100)
    knowledgeList.value = response.items
  } catch (error) {
    ElMessage.error('加载知识库列表失败')
    console.error(error)
  }
}

// 创建知识库
async function handleCreate() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }

  creating.value = true
  try {
    await createKnowledge(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.value = { name: '', description: '' }
    await loadKnowledgeList()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

// 删除知识库
async function handleDelete(knowledgeId: string) {
  try {
    await ElMessageBox.confirm('确定要删除该知识库吗？此操作不可恢复。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteKnowledge(knowledgeId)
    ElMessage.success('删除成功')
    await loadKnowledgeList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 批量删除
async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 个知识库吗？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const promises = selectedIds.value.map(id => deleteKnowledge(id))
    const results = await Promise.allSettled(promises)

    const failedCount = results.filter(r => r.status === 'rejected').length
    if (failedCount > 0) {
      ElMessage.warning(`已删除 ${selectedIds.value.length - failedCount} 个，${failedCount} 个删除失败`)
    } else {
      ElMessage.success(`成功删除 ${selectedIds.value.length} 个知识库`)
    }

    exitBatchMode()
    await loadKnowledgeList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

onMounted(() => {
  loadKnowledgeList()
})
</script>

<style scoped>@import '../styles/knowledge-page.css';</style>
