<template>
  <div class="memory-page">
    <div class="page-header">
      <h2>记忆管理</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        添加记忆
      </el-button>
    </div>

    <p class="page-desc">管理你的长期记忆，AI 在对话中会自动参考这些信息来更好地了解你。</p>

    <!-- 类型筛选 -->
    <div class="filter-bar">
      <el-radio-group v-model="filterType" size="default">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="fact">事实</el-radio-button>
        <el-radio-button label="preference">偏好</el-radio-button>
        <el-radio-button label="insight">洞察</el-radio-button>
      </el-radio-group>
      <span class="memory-count">共 {{ filteredMemories.length }} 条记忆</span>
    </div>

    <!-- 记忆列表 -->
    <div class="memory-list" v-loading="loading">
      <el-card
        v-for="memory in filteredMemories"
        :key="memory.memory_id"
        class="memory-card"
      >
        <div class="memory-card-body">
          <div class="memory-main">
            <el-tag
              :type="typeTagMap[memory.memory_type]?.type || 'info'"
              size="small"
              class="memory-type-tag"
            >
              {{ typeTagMap[memory.memory_type]?.label || memory.memory_type }}
            </el-tag>
            <span class="memory-content" v-if="editingId !== memory.memory_id">
              {{ memory.content }}
            </span>
            <el-input
              v-else
              v-model="editForm.content"
              type="textarea"
              :rows="2"
              placeholder="编辑记忆内容"
            />
          </div>
          <div class="memory-meta">
            <span class="memory-source" v-if="memory.source_dialog_id">
              来源: {{ memory.source_dialog_id === 'manual' ? '手动添加' : '对话提取' }}
            </span>
            <span class="memory-time" v-if="memory.created_at">
              {{ formatTime(memory.created_at) }}
            </span>
          </div>
        </div>
        <div class="memory-actions">
          <template v-if="editingId !== memory.memory_id">
            <el-button size="small" text @click="startEdit(memory)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button size="small" text type="danger" @click="handleDelete(memory.memory_id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
          <template v-else>
            <el-button size="small" type="primary" @click="handleUpdate(memory.memory_id)">
              保存
            </el-button>
            <el-button size="small" @click="cancelEdit">取消</el-button>
          </template>
        </div>
      </el-card>

      <el-empty v-if="!loading && filteredMemories.length === 0" description="暂无记忆" />
    </div>

    <!-- 添加记忆对话框 -->
    <el-dialog v-model="showAddDialog" title="添加记忆" width="500px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="类型" required>
          <el-select v-model="addForm.memory_type" placeholder="选择记忆类型">
            <el-option label="事实 (个人事实)" value="fact" />
            <el-option label="偏好 (个人偏好)" value="preference" />
            <el-option label="洞察 (重要洞察)" value="insight" />
          </el-select>
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
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
const filterType = ref('all')
const showAddDialog = ref(false)
const editingId = ref<string | null>(null)
const editForm = ref({ content: '', memory_type: '' })

const addForm = ref({
  content: '',
  memory_type: 'fact'
})

const typeTagMap: Record<string, { label: string; type: string }> = {
  fact: { label: '事实', type: 'primary' },
  preference: { label: '偏好', type: 'success' },
  insight: { label: '洞察', type: 'warning' }
}

const filteredMemories = computed(() => {
  if (filterType.value === 'all') return memoryList.value
  return memoryList.value.filter(m => m.memory_type === filterType.value)
})

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
    const res = await getMemoryList()
    memoryList.value = res.items || []
  } catch (error) {
    ElMessage.error('加载记忆列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
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
    addForm.value = { content: '', memory_type: 'fact' }
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
    memory_type: memory.memory_type
  }
}

function cancelEdit() {
  editingId.value = null
  editForm.value = { content: '', memory_type: '' }
}

async function handleUpdate(memoryId: string) {
  if (!editForm.value.content.trim()) {
    ElMessage.warning('记忆内容不能为空')
    return
  }
  try {
    await updateMemory(memoryId, {
      content: editForm.value.content,
      memory_type: editForm.value.memory_type
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

<style scoped>
.memory-page {
  padding: 32px;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  color: #1f2937;
  font-weight: 700;
}

.page-desc {
  color: #9ca3af;
  font-size: 14px;
  margin: 0 0 24px 0;
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.memory-count {
  font-size: 13px;
  color: #9ca3af;
}

.memory-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.memory-card {
  transition: all 0.2s ease;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.memory-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border-color: rgba(99, 102, 241, 0.2);
}

.memory-card :deep(.el-card__body) {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px 20px;
}

.memory-card-body {
  flex: 1;
  min-width: 0;
}

.memory-main {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.memory-type-tag {
  flex-shrink: 0;
  margin-top: 2px;
}

.memory-content {
  font-size: 15px;
  color: #1f2937;
  line-height: 1.6;
  word-break: break-word;
}

.memory-meta {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  padding-left: 68px;
  font-size: 12px;
  color: #9ca3af;
}

.memory-actions {
  flex-shrink: 0;
  display: flex;
  gap: 4px;
  margin-left: 12px;
}
</style>
