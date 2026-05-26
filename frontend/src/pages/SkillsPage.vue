<template>
  <div class="skills-page">
    <div class="skills-page-inner">
    <!-- 顶部 Banner -->
    <div class="skills-banner">
      <div class="banner-content">
        <div class="banner-info">
          <div class="banner-icon">
            <el-icon :size="28" color="#fff"><SetUp /></el-icon>
          </div>
          <div class="banner-text">
            <h2>技能管理</h2>
            <p>管理和配置 AI 的技能，让 AI 具备更多专业能力</p>
          </div>
        </div>
        <div class="banner-actions">
          <el-button size="large" round @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            上传技能包
          </el-button>
          <el-button type="primary" size="large" round @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加技能
          </el-button>
        </div>
      </div>
    </div>

    <!-- 搜索与操作栏 -->
    <div class="skills-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索技能名称..."
          :prefix-icon="Search"
          clearable
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
            :disabled="selectedNames.length === 0"
            @click="handleBatchDelete"
          >
            <el-icon><Delete /></el-icon>
            删除选中 ({{ selectedNames.length }})
          </el-button>
          <el-button type="default" @click="exitBatchMode">退出批量</el-button>
        </template>
      </div>
    </div>

    <!-- 技能列表 -->
    <div class="skills-list" v-loading="loading">
      <div
        v-for="skill in skillList"
        :key="skill.name"
        class="skill-card"
        :class="{ 'card-selected': selectedNames.includes(skill.name), 'card-selectable': batchMode }"
        @click="handleCardClick(skill)"
      >
        <div class="card-color-bar"></div>
        <div class="card-body">
          <div class="card-header">
            <div v-if="batchMode" class="card-checkbox" @click.stop="toggleSelect(skill.name)">
              <el-checkbox :model-value="selectedNames.includes(skill.name)" />
            </div>
            <div class="card-icon">
              <el-icon :size="20" color="#6366f1"><SetUp /></el-icon>
            </div>
            <div class="card-title-area">
              <h3>{{ skill.name }}</h3>
              <p class="card-description">{{ skill.description || '暂无描述' }}</p>
            </div>
          </div>
          <div class="card-footer">
            <div class="card-meta">
              <span class="meta-item">
                <el-icon :size="12"><Folder /></el-icon>
                {{ skill.dir_name }}
              </span>
            </div>
            <div class="card-actions" v-if="!batchMode">
              <div class="action-icon-btn danger" @click="handleDelete(skill.name)">
                <el-icon :size="14"><Delete /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!loading && skillList.length === 0 && searchKeyword.trim()" class="empty-state">
        <div class="empty-icon">🔍</div>
        <p class="empty-title">未找到匹配的技能</p>
        <p class="empty-desc">尝试使用其他关键词搜索</p>
      </div>

      <div v-if="!loading && skillList.length === 0 && !searchKeyword.trim()" class="empty-state">
        <div class="empty-icon">⚡</div>
        <p class="empty-title">暂无技能</p>
        <p class="empty-desc">点击上方按钮添加你的第一个技能</p>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-bar" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadSkills"
      />
    </div>

    <!-- 添加技能对话框 -->
    <el-dialog v-model="showAddDialog" title="添加技能" width="560px" :close-on-click-modal="false">
      <el-form :model="addForm" label-width="100px">
        <el-form-item label="技能名称" required>
          <el-input v-model="addForm.name" placeholder="仅允许字母、数字、连字符和下划线" />
        </el-form-item>
        <el-form-item label="技能描述">
          <el-input
            v-model="addForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入技能描述（可选）"
          />
        </el-form-item>
        <el-form-item label="SKILL.md">
          <el-input
            v-model="addForm.skill_md_content"
            type="textarea"
            :rows="8"
            placeholder="自定义 SKILL.md 内容（可选，不填则自动生成）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAdd" :loading="adding">添加</el-button>
      </template>
    </el-dialog>

    <!-- 上传技能包对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传技能包" width="500px" :close-on-click-modal="false">
      <el-form label-width="100px">
        <el-form-item label="技能包" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".zip"
            :on-change="handleFileChange"
            :on-remove="() => uploadFile = null"
          >
            <el-button size="small">
              <el-icon><Upload /></el-icon>
              选择 ZIP 文件
            </el-button>
            <template #tip>
              <div class="upload-tip">仅支持 .zip 格式，包内应包含 SKILL.md（含 name 和 description）</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Upload, Search, SetUp, Folder, Select } from '@element-plus/icons-vue'
import type { UploadFile as ElUploadFile } from 'element-plus'
import {
  getSkillList,
  addSkill,
  uploadSkill,
  deleteSkill,
  type SkillInfo
} from '../apis/skills'

const skillList = ref<SkillInfo[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)
const searchKeyword = ref('')
const batchMode = ref(false)
const selectedNames = ref<string[]>([])

// 添加技能
const showAddDialog = ref(false)
const adding = ref(false)
const addForm = ref({
  name: '',
  description: '',
  skill_md_content: ''
})

// 上传技能包
const showUploadDialog = ref(false)
const uploading = ref(false)
const uploadFile = ref<File | null>(null)
const uploadRef = ref()

// 防抖定时器
let debounceTimer: ReturnType<typeof setTimeout> | null = null

// 是否全选
const isAllSelected = computed(() => {
  return skillList.value.length > 0 && skillList.value.every(s => selectedNames.value.includes(s.name))
})

// 输入即搜索（防抖 300ms）
watch(searchKeyword, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    loadSkills()
  }, 300)
})

// 进入批量模式
function enterBatchMode() {
  batchMode.value = true
  selectedNames.value = []
}

// 退出批量模式
function exitBatchMode() {
  batchMode.value = false
  selectedNames.value = []
}

// 切换选中
function toggleSelect(name: string) {
  const idx = selectedNames.value.indexOf(name)
  if (idx >= 0) {
    selectedNames.value.splice(idx, 1)
  } else {
    selectedNames.value.push(name)
  }
}

// 全选/取消全选
function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedNames.value = []
  } else {
    selectedNames.value = skillList.value.map(s => s.name)
  }
}

// 卡片点击：批量模式下切换选中
function handleCardClick(skill: SkillInfo) {
  if (batchMode.value) {
    toggleSelect(skill.name)
  }
}

// 加载技能列表
async function loadSkills() {
  loading.value = true
  try {
    const res = await getSkillList(currentPage.value, pageSize.value, searchKeyword.value)
    skillList.value = res.items
    total.value = res.total
  } catch (error) {
    ElMessage.error('加载技能列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 添加技能
async function handleAdd() {
  if (!addForm.value.name.trim()) {
    ElMessage.warning('请输入技能名称')
    return
  }

  adding.value = true
  try {
    await addSkill(addForm.value)
    ElMessage.success('技能添加成功')
    showAddDialog.value = false
    addForm.value = { name: '', description: '', skill_md_content: '' }
    await loadSkills()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  } finally {
    adding.value = false
  }
}

// 上传文件选择
function handleFileChange(file: ElUploadFile) {
  if (file.raw) {
    uploadFile.value = file.raw
  }
}

// 上传技能包
async function handleUpload() {
  if (!uploadFile.value) {
    ElMessage.warning('请选择 ZIP 文件')
    return
  }

  uploading.value = true
  try {
    await uploadSkill(uploadFile.value)
    ElMessage.success('技能包上传成功')
    showUploadDialog.value = false
    uploadFile.value = null
    await loadSkills()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

// 删除技能
async function handleDelete(skillName: string) {
  try {
    await ElMessageBox.confirm(`确定要删除技能「${skillName}」吗？此操作不可恢复。`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteSkill(skillName)
    ElMessage.success('删除成功')
    await loadSkills()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 批量删除
async function handleBatchDelete() {
  if (selectedNames.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedNames.value.length} 个技能吗？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const promises = selectedNames.value.map(name => deleteSkill(name))
    const results = await Promise.allSettled(promises)

    const failedCount = results.filter(r => r.status === 'rejected').length
    if (failedCount > 0) {
      ElMessage.warning(`已删除 ${selectedNames.value.length - failedCount} 个，${failedCount} 个删除失败`)
    } else {
      ElMessage.success(`成功删除 ${selectedNames.value.length} 个技能`)
    }

    exitBatchMode()
    await loadSkills()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

onMounted(() => {
  loadSkills()
})

onUnmounted(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
})
</script>

<style scoped>@import '../styles/skills-page.css';</style>
