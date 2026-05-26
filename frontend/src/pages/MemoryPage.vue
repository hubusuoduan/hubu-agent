<template>
  <div class="memory-page">
    <div class="memory-page-inner">
    <!-- 顶部 Banner -->
    <div class="memory-banner">
      <div class="banner-content">
        <div class="banner-info">
          <div class="banner-icon">
            <el-icon :size="28" color="#fff"><Collection /></el-icon>
          </div>
          <div class="banner-text">
            <h2>记忆管理</h2>
            <p>管理你的长期记忆，AI 在对话中会自动参考这些信息来更好地了解你</p>
          </div>
        </div>
        <el-button type="primary" size="large" round @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加记忆
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #09b572, #059669);">
          <el-icon :size="20" color="#fff"><Collection /></el-icon>
        </div>
        <div class="stat-detail">
          <span class="stat-value">{{ totalCount }}</span>
          <span class="stat-label">全部记忆</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #3b82f6, #2563eb);">
          <el-icon :size="20" color="#fff"><Document /></el-icon>
        </div>
        <div class="stat-detail">
          <span class="stat-value">{{ typeCounts.fact }}</span>
          <span class="stat-label">事实</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #f59e0b, #d97706);">
          <el-icon :size="20" color="#fff"><Star /></el-icon>
        </div>
        <div class="stat-detail">
          <span class="stat-value">{{ typeCounts.preference }}</span>
          <span class="stat-label">偏好</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #8b5cf6, #7c3aed);">
          <el-icon :size="20" color="#fff"><TrendCharts /></el-icon>
        </div>
        <div class="stat-detail">
          <span class="stat-value">{{ typeCounts.insight }}</span>
          <span class="stat-label">洞察</span>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索记忆内容..."
          :prefix-icon="Search"
          clearable
          style="width: 280px"
          @input="handleSearch"
        />
        <div class="filter-tabs">
          <div
            :class="['filter-tab', { active: filterType === 'all' }]"
            @click="filterType = 'all'; handleFilterChange()"
          >全部</div>
          <div
            :class="['filter-tab', { active: filterType === 'fact' }]"
            @click="filterType = 'fact'; handleFilterChange()"
          >
            <span class="tab-dot" style="background: #3b82f6;"></span>
            事实
          </div>
          <div
            :class="['filter-tab', { active: filterType === 'preference' }]"
            @click="filterType = 'preference'; handleFilterChange()"
          >
            <span class="tab-dot" style="background: #f59e0b;"></span>
            偏好
          </div>
          <div
            :class="['filter-tab', { active: filterType === 'insight' }]"
            @click="filterType = 'insight'; handleFilterChange()"
          >
            <span class="tab-dot" style="background: #8b5cf6;"></span>
            洞察
          </div>
        </div>
      </div>
    </div>

    <!-- 记忆列表 -->
    <div class="memory-list" v-loading="loading">
      <div
        v-for="memory in memoryList"
        :key="memory.memory_id"
        :class="['memory-card', `type-${memory.memory_type}`]"
      >
        <div class="card-color-bar"></div>
        <div class="card-body">
          <div class="card-header">
            <div :class="['type-badge', `badge-${memory.memory_type}`]">
              <span class="badge-icon">{{ typeTagMap[memory.memory_type]?.icon || '📌' }}</span>
              {{ typeTagMap[memory.memory_type]?.label || memory.memory_type }}
            </div>
            <div class="card-importance" v-if="editingId !== memory.memory_id">
              <el-icon
                v-for="i in 5"
                :key="i"
                :class="{ 'star-active': i <= memory.importance }"
              ><Star /></el-icon>
            </div>
            <el-rate v-else v-model="editForm.importance" :max="5" size="small" />
          </div>
          <div class="card-content" v-if="editingId !== memory.memory_id">
            {{ memory.content }}
          </div>
          <el-input
            v-else
            v-model="editForm.content"
            type="textarea"
            :rows="2"
            placeholder="编辑记忆内容"
          />
          <div class="card-footer">
            <div class="card-meta">
              <span v-if="memory.source_dialog_id" class="meta-item">
                <el-icon :size="12"><ChatDotRound /></el-icon>
                {{ memory.source_dialog_id === 'manual' ? '手动添加' : '对话提取' }}
              </span>
              <span v-if="memory.created_at" class="meta-item">
                <el-icon :size="12"><Clock /></el-icon>
                {{ formatTime(memory.created_at) }}
              </span>
            </div>
            <div class="card-actions">
              <template v-if="editingId !== memory.memory_id">
                <div class="action-icon-btn" @click="startEdit(memory)">
                  <el-icon :size="14"><Edit /></el-icon>
                </div>
                <div class="action-icon-btn danger" @click="handleDelete(memory.memory_id)">
                  <el-icon :size="14"><Delete /></el-icon>
                </div>
              </template>
              <template v-else>
                <el-button size="small" type="primary" round @click="handleUpdate(memory.memory_id)">保存</el-button>
                <el-button size="small" round @click="cancelEdit">取消</el-button>
              </template>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!loading && memoryList.length === 0" class="empty-state">
        <div class="empty-icon">🧠</div>
        <p class="empty-title">暂无记忆</p>
        <p class="empty-desc">点击上方按钮添加你的第一条记忆</p>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-bar" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 添加记忆对话框 -->
    <el-dialog v-model="showAddDialog" title="添加记忆" width="500px" :close-on-click-modal="false">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="类型" required>
          <el-select v-model="addForm.memory_type" placeholder="选择记忆类型" style="width: 100%;">
            <el-option label="📌 事实 — 个人事实" value="fact" />
            <el-option label="⭐ 偏好 — 个人偏好" value="preference" />
            <el-option label="💡 洞察 — 重要洞察" value="insight" />
          </el-select>
        </el-form-item>
        <el-form-item label="重要性">
          <el-rate v-model="addForm.importance" :max="5" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input
            v-model="addForm.content"
            type="textarea"
            :rows="3"
            placeholder="例如：我是湖北大学计算机专业的学生"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAdd" :loading="adding">添加</el-button>
      </template>
    </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Search, Star, Collection, Document, TrendCharts, ChatDotRound, Clock } from '@element-plus/icons-vue'
import {
  getMemoryList,
  createMemory,
  updateMemory,
  deleteMemory,
  type Memory
} from '../apis/memory'

const loading = ref(false)
const adding = ref(false)
const memoryList = ref<Memory[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filterType = ref('all')
const searchKeyword = ref('')
const showAddDialog = ref(false)
const editingId = ref<string | null>(null)
const editForm = ref({ content: '', memory_type: '', importance: 3 })

let searchTimer: ReturnType<typeof setTimeout> | null = null

const addForm = ref({
  content: '',
  memory_type: 'fact',
  importance: 3
})

const typeTagMap: Record<string, { label: string; type: string; icon: string }> = {
  fact: { label: '事实', type: 'primary', icon: '📌' },
  preference: { label: '偏好', type: 'success', icon: '⭐' },
  insight: { label: '洞察', type: 'warning', icon: '💡' }
}

const typeCounts = ref({ fact: 0, preference: 0, insight: 0 })
const totalCount = ref(0)

async function loadTypeCounts() {
  try {
    const [allRes, factRes, prefRes, insightRes] = await Promise.all([
      getMemoryList({ page: 1, page_size: 1 }),
      getMemoryList({ page: 1, page_size: 1, memory_type: 'fact' }),
      getMemoryList({ page: 1, page_size: 1, memory_type: 'preference' }),
      getMemoryList({ page: 1, page_size: 1, memory_type: 'insight' })
    ])
    totalCount.value = allRes.total || 0
    typeCounts.value = {
      fact: factRes.total || 0,
      preference: prefRes.total || 0,
      insight: insightRes.total || 0
    }
  } catch {
    // 静默失败
  }
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function loadMemories() {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterType.value !== 'all') {
      params.memory_type = filterType.value
    }
    if (searchKeyword.value.trim()) {
      params.keyword = searchKeyword.value.trim()
    }
    const res = await getMemoryList(params)
    memoryList.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    ElMessage.error('加载记忆列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
  await loadTypeCounts()
}

function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadMemories()
  }, 300)
}

function handleFilterChange() {
  currentPage.value = 1
  loadMemories()
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadMemories()
}

async function handleAdd() {
  if (!addForm.value.content.trim()) {
    ElMessage.warning('请输入记忆内容')
    return
  }
  adding.value = true
  try {
    await createMemory(addForm.value)
    ElMessage.success('添加成功')
    showAddDialog.value = false
    addForm.value = { content: '', memory_type: 'fact', importance: 3 }
    await loadMemories()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  } finally {
    adding.value = false
  }
}

function startEdit(memory: Memory) {
  editingId.value = memory.memory_id
  editForm.value = {
    content: memory.content,
    memory_type: memory.memory_type,
    importance: memory.importance || 3
  }
}

function cancelEdit() {
  editingId.value = null
  editForm.value = { content: '', memory_type: '', importance: 3 }
}

async function handleUpdate(memoryId: string) {
  if (!editForm.value.content.trim()) {
    ElMessage.warning('记忆内容不能为空')
    return
  }
  try {
    await updateMemory(memoryId, {
      content: editForm.value.content,
      memory_type: editForm.value.memory_type,
      importance: editForm.value.importance
    })
    ElMessage.success('更新成功')
    editingId.value = null
    await loadMemories()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  }
}

async function handleDelete(memoryId: string) {
  try {
    await ElMessageBox.confirm('确定要删除这条记忆吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteMemory(memoryId)
    ElMessage.success('删除成功')
    await loadMemories()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadMemories()
})
</script>

<style scoped>@import '../styles/memory-page.css';</style>
