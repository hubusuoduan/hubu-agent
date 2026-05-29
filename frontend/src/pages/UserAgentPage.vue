<template>
  <div class="user-agent-page">
    <div class="user-agent-page-inner">
      <!-- 顶部 Banner -->
      <div class="agent-banner">
        <div class="banner-content">
          <div class="banner-info">
            <div class="banner-icon">
              <el-icon :size="28" color="#fff"><MagicStick /></el-icon>
            </div>
            <div class="banner-text">
              <h2>自定义 Agent</h2>
              <p>创建专属 AI Agent，赋予独特能力，让 AI 更懂你的需求</p>
            </div>
          </div>
          <div class="banner-actions">
            <el-button type="primary" size="large" round @click="openCreateDialog">
              <el-icon><Plus /></el-icon>
              创建 Agent
            </el-button>
          </div>
        </div>
      </div>

      <!-- 搜索栏 -->
      <div class="agent-toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索 Agent 名称..."
            :prefix-icon="Search"
            clearable
            class="search-input"
          />
        </div>
      </div>

      <!-- Agent 列表 -->
      <div class="agent-list" v-loading="loading">
        <div
          v-for="agent in filteredAgents"
          :key="agent.id"
          class="agent-card"
        >
          <div class="card-color-bar" :class="{ disabled: agent.enabled === 0 }"></div>
          <div class="card-body">
            <div class="card-header">
              <div class="card-icon" :class="{ disabled: agent.enabled === 0 }">
                <el-icon :size="20" color="#6366f1"><MagicStick /></el-icon>
              </div>
              <div class="card-title-area">
                <div class="title-row">
                  <h3>{{ agent.display_name }}</h3>
                  <el-tag size="small" :type="agent.enabled === 1 ? 'success' : 'info'" class="status-tag">
                    {{ agent.enabled === 1 ? '已启用' : '已禁用' }}
                  </el-tag>
                </div>
                <p class="card-name">@{{ agent.name }}</p>
                <p class="card-description">{{ agent.description || '暂无描述' }}</p>
              </div>
            </div>
            <div class="card-footer">
              <div class="card-meta">
                <span class="meta-item" v-if="agent.tools.length > 0">
                  <el-icon :size="12"><SetUp /></el-icon>
                  {{ agent.tools.length }} 个工具
                </span>
                <span class="meta-item" v-else>
                  <el-icon :size="12"><SetUp /></el-icon>
                  无工具
                </span>
                <span class="meta-item">
                  <el-icon :size="12"><Clock /></el-icon>
                  {{ formatTime(agent.update_time) }}
                </span>
              </div>
              <div class="card-actions">
                <el-tooltip :content="agent.enabled === 1 ? '禁用' : '启用'" placement="top">
                  <div class="action-icon-btn" @click="handleToggleEnabled(agent)">
                    <el-icon :size="14"><Open v-if="agent.enabled === 1" /><TurnOff v-else /></el-icon>
                  </div>
                </el-tooltip>
                <el-tooltip content="编辑" placement="top">
                  <div class="action-icon-btn" @click="openEditDialog(agent)">
                    <el-icon :size="14"><Edit /></el-icon>
                  </div>
                </el-tooltip>
                <el-tooltip content="删除" placement="top">
                  <div class="action-icon-btn danger" @click="handleDelete(agent)">
                    <el-icon :size="14"><Delete /></el-icon>
                  </div>
                </el-tooltip>
              </div>
            </div>
          </div>
        </div>

        <div v-if="!loading && filteredAgents.length === 0 && searchKeyword.trim()" class="empty-state">
          <div class="empty-icon">🔍</div>
          <p class="empty-title">未找到匹配的 Agent</p>
          <p class="empty-desc">尝试使用其他关键词搜索</p>
        </div>

        <div v-if="!loading && agentList.length === 0 && !searchKeyword.trim()" class="empty-state">
          <div class="empty-icon">✨</div>
          <p class="empty-title">暂无自定义 Agent</p>
          <p class="empty-desc">点击上方按钮创建你的第一个 Agent</p>
        </div>
      </div>

      <!-- 创建/编辑 Agent 对话框 -->
      <el-dialog
        v-model="showDialog"
        :title="isEditing ? '编辑 Agent' : '创建 Agent'"
        width="680px"
        :close-on-click-modal="false"
        @closed="resetForm"
      >
        <el-form :model="formData" :rules="formRules" ref="formRef" label-width="110px">
          <el-form-item label="Agent 名称" prop="name">
            <el-input
              v-model="formData.name"
              placeholder="英文名称，如 translator"
              :disabled="isEditing"
              maxlength="64"
              show-word-limit
            />
            <div class="form-tip" v-if="!isEditing">只允许字母开头，包含字母、数字、下划线，创建后不可修改</div>
          </el-form-item>
          <el-form-item label="显示名" prop="display_name">
            <el-input v-model="formData.display_name" placeholder="如：翻译官" maxlength="128" show-word-limit />
          </el-form-item>
          <el-form-item label="描述" prop="description">
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="2"
              placeholder="简短描述 Agent 的能力，如：擅长中英互译，保持原文语义和风格"
              maxlength="512"
              show-word-limit
            />
            <div class="form-tip">描述会展示给 Supervisor 用于路由决策，请尽量准确</div>
          </el-form-item>
          <el-form-item label="可用工具" prop="tools">
            <el-select
              v-model="formData.tools"
              multiple
              filterable
              placeholder="选择 Agent 可使用的工具"
              class="tool-select"
            >
              <el-option
                v-for="tool in availableTools"
                :key="tool.name"
                :label="tool.name"
                :value="tool.name"
              >
                <div class="tool-option">
                  <span class="tool-option-name">{{ tool.name }}</span>
                  <span class="tool-option-desc">{{ tool.description.slice(0, 60) }}</span>
                </div>
              </el-option>
            </el-select>
            <div class="form-tip">从已有工具池中选择，不选则 Agent 无工具（纯对话型）</div>
          </el-form-item>
          <el-form-item label="System Prompt" prop="system_prompt">
            <el-input
              v-model="formData.system_prompt"
              type="textarea"
              :rows="8"
              placeholder="定义 Agent 的角色、行为和注意事项，如：\n你是一个专业翻译官，擅长中英互译。\n\n你的特点:\n- 精通中英文语法\n- 翻译时保持原文语义和风格"
            />
            <div class="form-tip">这是 Agent 的核心指令，决定它的行为方式</div>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEditing ? '保存' : '创建' }}
          </el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Delete, Search, MagicStick, SetUp, Edit, Open, TurnOff, Clock
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import {
  getUserAgentList,
  createUserAgent,
  updateUserAgent,
  deleteUserAgent,
  getAvailableTools,
  type UserAgentInfo,
  type ToolInfo,
} from '../apis/user-agent'

const agentList = ref<UserAgentInfo[]>([])
const availableTools = ref<ToolInfo[]>([])
const loading = ref(false)
const searchKeyword = ref('')

// 对话框
const showDialog = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const formData = ref({
  name: '',
  display_name: '',
  description: '',
  system_prompt: '',
  tools: [] as string[],
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入 Agent 名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '只允许字母开头，包含字母、数字、下划线', trigger: 'blur' },
  ],
  display_name: [
    { required: true, message: '请输入显示名', trigger: 'blur' },
  ],
  description: [
    { required: true, message: '请输入描述', trigger: 'blur' },
  ],
  system_prompt: [
    { required: true, message: '请输入 System Prompt', trigger: 'blur' },
  ],
}

// 搜索过滤
const filteredAgents = computed(() => {
  if (!searchKeyword.value.trim()) return agentList.value
  const kw = searchKeyword.value.toLowerCase()
  return agentList.value.filter(a =>
    a.name.toLowerCase().includes(kw) ||
    a.display_name.toLowerCase().includes(kw) ||
    a.description.toLowerCase().includes(kw)
  )
})

// 格式化时间
function formatTime(timeStr: string | null) {
  if (!timeStr) return '刚刚'
  const d = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + ' 分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + ' 小时前'
  return d.toLocaleDateString()
}

// 加载 Agent 列表
async function loadAgents() {
  loading.value = true
  try {
    const res = await getUserAgentList()
    agentList.value = res.items
  } catch (error) {
    ElMessage.error('加载 Agent 列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 加载可用工具
async function loadTools() {
  try {
    const res = await getAvailableTools()
    availableTools.value = res.tools
  } catch (error) {
    console.error('加载工具列表失败', error)
  }
}

// 打开创建对话框
function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  formData.value = {
    name: '',
    display_name: '',
    description: '',
    system_prompt: '',
    tools: [],
  }
  showDialog.value = true
}

// 打开编辑对话框
function openEditDialog(agent: UserAgentInfo) {
  isEditing.value = true
  editingId.value = agent.id
  formData.value = {
    name: agent.name,
    display_name: agent.display_name,
    description: agent.description,
    system_prompt: '', // 需要从详情获取
    tools: [...agent.tools],
  }
  // 获取详情以拿到 system_prompt
  loadAgentDetail(agent.id)
  showDialog.value = true
}

// 加载 Agent 详情（获取 system_prompt）
async function loadAgentDetail(agentId: number) {
  try {
    const detail = await getUserAgent(agentId)
    if (detail.system_prompt) {
      formData.value.system_prompt = detail.system_prompt
    }
  } catch (error) {
    console.error(error)
  }
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEditing.value && editingId.value) {
        await updateUserAgent(editingId.value, {
          display_name: formData.value.display_name,
          description: formData.value.description,
          system_prompt: formData.value.system_prompt || undefined,
          tools: formData.value.tools,
        })
        ElMessage.success('Agent 更新成功')
      } else {
        await createUserAgent(formData.value)
        ElMessage.success('Agent 创建成功')
      }
      showDialog.value = false
      await loadAgents()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 切换启用/禁用
async function handleToggleEnabled(agent: UserAgentInfo) {
  const newEnabled = agent.enabled === 1 ? 0 : 1
  try {
    await updateUserAgent(agent.id, { enabled: newEnabled })
    ElMessage.success(newEnabled === 1 ? '已启用' : '已禁用')
    await loadAgents()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

// 删除 Agent
async function handleDelete(agent: UserAgentInfo) {
  try {
    await ElMessageBox.confirm(
      `确定要删除 Agent「${agent.display_name}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteUserAgent(agent.id)
    ElMessage.success('删除成功')
    await loadAgents()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 重置表单
function resetForm() {
  formData.value = {
    name: '',
    display_name: '',
    description: '',
    system_prompt: '',
    tools: [],
  }
  formRef.value?.resetFields()
}

onMounted(() => {
  loadAgents()
  loadTools()
})
</script>

<style>
@import '../styles/user-agent-page.css';
</style>
