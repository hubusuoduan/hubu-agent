<template>
  <div class="settings-page">
    <div class="settings-page-inner">
    <!-- 顶部 Banner -->
    <div class="settings-banner">
      <div class="banner-content">
        <div class="banner-info">
          <div class="banner-icon">
            <el-icon :size="28" color="#fff"><Setting /></el-icon>
          </div>
          <div class="banner-text">
            <h2>系统设置</h2>
            <p>调整系统运行参数，修改后即时生效</p>
          </div>
        </div>
        <el-button @click="handleResetAll" type="danger" plain size="large" round>
          <el-icon><RefreshLeft /></el-icon>
          重置全部
        </el-button>
      </div>
    </div>

    <div v-loading="loading" class="settings-content">
      <!-- Embedding 供应商配置 -->
      <div class="settings-group embedding-group">
        <div class="group-header">
          <div class="group-icon-wrapper">
            <span class="group-icon">🔗</span>
          </div>
          <span class="group-title">Embedding 供应商</span>
          <span class="group-count">{{ embeddingProvider ? '已配置' : '未配置' }}</span>
        </div>

        <div class="group-items">
          <!-- 未配置状态 -->
          <div v-if="!embeddingProvider" class="embedding-empty">
            <p>尚未配置 Embedding 供应商，知识库功能将不可用</p>
            <el-button type="primary" size="small" @click="openEmbeddingDialog(false)" style="background: #0891b2; border-color: #0891b2;">
              配置 Embedding
            </el-button>
          </div>

          <!-- 已配置状态 -->
          <div v-else class="embedding-info">
            <div class="setting-item">
              <div class="setting-row">
                <div class="setting-label">
                  <span class="setting-name">模型</span>
                  <span class="setting-key">EMBEDDING_MODEL</span>
                </div>
                <div class="setting-control">
                  <span class="embedding-value">{{ embeddingProvider.model }}</span>
                  <el-button size="small" @click="openEmbeddingDialog(true)">编辑</el-button>
                  <el-button size="small" type="danger" plain @click="handleDeleteEmbedding">删除</el-button>
                </div>
              </div>
            </div>
            <div class="setting-item">
              <div class="setting-row">
                <div class="setting-label">
                  <span class="setting-name">API Key</span>
                  <span class="setting-key">EMBEDDING_API_KEY</span>
                </div>
                <div class="setting-control">
                  <span class="embedding-value masked">{{ embeddingDetail?.api_key || '****' }}</span>
                </div>
              </div>
            </div>
            <div class="setting-item">
              <div class="setting-row">
                <div class="setting-label">
                  <span class="setting-name">Base URL</span>
                  <span class="setting-key">EMBEDDING_BASE_URL</span>
                </div>
                <div class="setting-control">
                  <span class="embedding-value url">{{ embeddingDetail?.base_url || '-' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统配置 -->
      <template v-for="(items, group) in groupedSettings" :key="group">
        <div class="settings-group">
          <div class="group-header">
            <div class="group-icon-wrapper">
              <span class="group-icon">{{ groupIconMap[group] || '⚙️' }}</span>
            </div>
            <span class="group-title">{{ group }}</span>
            <span class="group-count">{{ items.length }} 项</span>
          </div>

          <div class="group-items">
            <div
              v-for="item in items"
              :key="item.key"
              :class="['setting-item', { modified: item.is_modified }]"
            >
              <div class="setting-row">
                <div class="setting-label">
                  <span class="setting-name">{{ item.desc }}</span>
                  <span class="setting-key">{{ item.key }}</span>
                </div>

                <div class="setting-control">
                  <!-- 布尔类型：开关 -->
                  <el-switch
                    v-if="item.type === 'bool'"
                    :model-value="item.current_value"
                    @change="(val: any) => handleUpdate(item, val)"
                    active-text="开"
                    inactive-text="关"
                  />

                  <!-- 整数类型：滑块 + 数字输入 -->
                  <div v-else-if="item.type === 'int'" class="number-control">
                    <el-slider
                      :model-value="item.current_value"
                      :min="item.min ?? 0"
                      :max="item.max ?? 100"
                      :step="getStep(item)"
                      :show-tooltip="false"
                      @input="(val: any) => item.current_value = val"
                      @change="(val: any) => handleUpdate(item, val)"
                    />
                    <el-input-number
                      :model-value="item.current_value"
                      :min="item.min ?? 0"
                      :max="item.max ?? 100"
                      :step="getStep(item)"
                      size="small"
                      controls-position="right"
                      style="width: 110px"
                      @change="(val: any) => handleUpdate(item, val)"
                    />
                  </div>

                  <!-- 浮点类型：滑块 + 数字输入 -->
                  <div v-else-if="item.type === 'float'" class="number-control">
                    <el-slider
                      :model-value="item.current_value"
                      :min="item.min ?? 0"
                      :max="item.max ?? 1"
                      :step="0.01"
                      :show-tooltip="false"
                      @input="(val: any) => item.current_value = val"
                      @change="(val: any) => handleUpdate(item, val)"
                    />
                    <el-input-number
                      :model-value="item.current_value"
                      :min="item.min ?? 0"
                      :max="item.max ?? 1"
                      :step="0.01"
                      :precision="2"
                      size="small"
                      controls-position="right"
                      style="width: 110px"
                      @change="(val: any) => handleUpdate(item, val)"
                    />
                  </div>

                  <!-- 字符串类型：文本输入 -->
                  <el-input
                    v-else-if="item.type === 'str' && item.key !== 'RAG_HYBRID_WEIGHTS'"
                    :model-value="item.current_value"
                    size="small"
                    style="width: 180px"
                    @change="(val: any) => handleUpdate(item, val)"
                  />

                  <!-- RAG_HYBRID_WEIGHTS 特殊双滑块 -->
                  <div v-else-if="item.key === 'RAG_HYBRID_WEIGHTS'" class="hybrid-weights-control">
                    <div class="weight-row">
                      <span class="weight-label">BM25</span>
                      <el-slider
                        v-model="hybridWeights.bm25"
                        :min="0" :max="1" :step="0.05"
                        :show-tooltip="false"
                        style="flex: 1; margin: 0 8px"
                        @change="onHybridWeightChange(item, 'bm25')"
                      />
                      <el-input-number
                        v-model="hybridWeights.bm25"
                        :min="0" :max="1" :step="0.05" :precision="2"
                        size="small" controls-position="right"
                        style="width: 90px"
                        @change="onHybridWeightChange(item, 'bm25')"
                      />
                    </div>
                    <div class="weight-row">
                      <span class="weight-label">语义</span>
                      <el-slider
                        v-model="hybridWeights.semantic"
                        :min="0" :max="1" :step="0.05"
                        :show-tooltip="false"
                        style="flex: 1; margin: 0 8px"
                        @change="onHybridWeightChange(item, 'semantic')"
                      />
                      <el-input-number
                        v-model="hybridWeights.semantic"
                        :min="0" :max="1" :step="0.05" :precision="2"
                        size="small" controls-position="right"
                        style="width: 90px"
                        @change="onHybridWeightChange(item, 'semantic')"
                      />
                    </div>
                  </div>

                  <!-- 重置按钮 -->
                  <el-tooltip content="重置为默认值" placement="top" :show-after="300">
                    <el-button
                      v-if="item.is_modified"
                      class="reset-btn"
                      size="small"
                      circle
                      @click="handleReset(item)"
                    >
                      <el-icon><RefreshLeft /></el-icon>
                    </el-button>
                  </el-tooltip>
                </div>
              </div>

              <!-- 默认值提示 -->
              <div v-if="item.is_modified" class="setting-hint">
                <el-icon :size="12"><InfoFilled /></el-icon>
                默认值：{{ item.default_value }}
              </div>
            </div>
          </div>
        </div>
      </template>

      <el-empty v-if="!loading && Object.keys(groupedSettings).length === 0" description="暂无可配置项" />
    </div>
    </div>

    <!-- Embedding 配置对话框 -->
    <el-dialog
      v-model="embeddingDialogVisible"
      :title="isEditingEmbedding ? '编辑 Embedding 供应商' : '配置 Embedding 供应商'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form :model="embeddingForm" :rules="embeddingFormRules" ref="embeddingFormRef" label-width="100px">
        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="embeddingForm.api_key"
            :placeholder="isEditingEmbedding ? '不修改请保持原值，修改请输入新的 API Key' : 'sk-xxx'"
            show-password
          />
        </el-form-item>
        <el-form-item label="Base URL" prop="base_url">
          <el-input v-model="embeddingForm.base_url" placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1" />
        </el-form-item>
        <el-form-item label="模型名称" prop="model">
          <el-input v-model="embeddingForm.model" placeholder="text-embedding-v3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="embeddingDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEmbeddingSubmit" :loading="embeddingSubmitting">
          {{ isEditingEmbedding ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshLeft, Setting, InfoFilled } from '@element-plus/icons-vue'
import {
  getSettings,
  updateSetting,
  resetSetting,
  resetAllSettings,
  type GroupedSettings,
  type SettingItem
} from '../apis/settings'
import {
  getEmbeddingProvider,
  getEmbeddingProviderDetail,
  createEmbeddingProvider,
  updateEmbeddingProvider,
  deleteEmbeddingProvider,
  type EmbeddingProviderInfo,
  type EmbeddingProviderDetail,
} from '../apis/embedding-provider'

const loading = ref(false)
const groupedSettings = ref<GroupedSettings>({})

// ===== Embedding Provider 状态 =====
const embeddingProvider = ref<EmbeddingProviderInfo | null>(null)
const embeddingDetail = ref<EmbeddingProviderDetail | null>(null)
const embeddingDialogVisible = ref(false)
const isEditingEmbedding = ref(false)
const embeddingSubmitting = ref(false)
const embeddingFormRef = ref()
const originalMaskedApiKey = ref('')

const embeddingForm = ref({
  api_key: '',
  base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  model: 'text-embedding-v3',
})

const embeddingFormRules = {
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }],
  model: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
}

async function loadEmbeddingProvider() {
  try {
    const res = await getEmbeddingProvider()
    embeddingProvider.value = res.provider || null
    if (embeddingProvider.value) {
      const detailRes = await getEmbeddingProviderDetail()
      embeddingDetail.value = detailRes.provider || null
    } else {
      embeddingDetail.value = null
    }
  } catch {
    embeddingProvider.value = null
    embeddingDetail.value = null
  }
}

function openEmbeddingDialog(editing: boolean) {
  isEditingEmbedding.value = editing
  if (editing && embeddingDetail.value) {
    embeddingForm.value = {
      api_key: embeddingDetail.value.api_key,
      base_url: embeddingDetail.value.base_url,
      model: embeddingDetail.value.model,
    }
    originalMaskedApiKey.value = embeddingDetail.value.api_key
  } else {
    embeddingForm.value = {
      api_key: '',
      base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      model: 'text-embedding-v3',
    }
    originalMaskedApiKey.value = ''
  }
  embeddingDialogVisible.value = true
}

async function handleEmbeddingSubmit() {
  try {
    await embeddingFormRef.value?.validate()
  } catch {
    return
  }

  embeddingSubmitting.value = true
  try {
    if (isEditingEmbedding.value) {
      const data: Record<string, any> = {}
      // api_key：如果用户没修改（仍是脱敏值），则不提交
      if (embeddingForm.value.api_key && embeddingForm.value.api_key !== originalMaskedApiKey.value) {
        data.api_key = embeddingForm.value.api_key
      }
      data.base_url = embeddingForm.value.base_url
      data.model = embeddingForm.value.model
      await updateEmbeddingProvider(data)
      ElMessage.success('Embedding 供应商已更新')
    } else {
      await createEmbeddingProvider(embeddingForm.value)
      ElMessage.success('Embedding 供应商已配置')
    }
    embeddingDialogVisible.value = false
    await loadEmbeddingProvider()
  } catch (e: any) {
    ElMessage.error((isEditingEmbedding.value ? '更新' : '配置') + '失败: ' + (e.message || '未知错误'))
  } finally {
    embeddingSubmitting.value = false
  }
}

async function handleDeleteEmbedding() {
  try {
    await ElMessageBox.confirm(
      '确定删除 Embedding 供应商配置吗？删除后知识库功能将不可用。',
      '确认删除',
      { type: 'warning' }
    )
    await deleteEmbeddingProvider()
    ElMessage.success('已删除')
    await loadEmbeddingProvider()
  } catch {
    // 取消删除
  }
}

const groupIconMap: Record<string, string> = {
  '对话历史': '💬',
  '上下文控制': '📏',
  'RAG检索': '🔍',
  '长期记忆': '🧠',
  'Agent': '🤖',
  '代码执行': '💻',
  'LLM': '🌐',
}

// RAG_HYBRID_WEIGHTS 双滑块联动
const hybridWeights = ref<{ bm25: number; semantic: number }>({ bm25: 0.4, semantic: 0.6 })

function initHybridWeights(item: SettingItem) {
  const parts = String(item.current_value).split(",").map(Number)
  hybridWeights.value = {
    bm25: isNaN(parts[0]) ? 0.4 : parts[0],
    semantic: isNaN(parts[1]) ? 0.6 : parts[1],
  }
}

function onHybridWeightChange(item: SettingItem, field: "bm25" | "semantic") {
  const val = hybridWeights.value[field]
  const clamped = Math.round(val * 100) / 100
  hybridWeights.value[field] = clamped
  const newValue = `${hybridWeights.value.bm25},${hybridWeights.value.semantic}`
  handleUpdate(item, newValue)
}

function getStep(item: SettingItem): number {
  const range = (item.max ?? 100) - (item.min ?? 0)
  if (range <= 10) return 1
  if (range <= 100) return 1
  if (range <= 1000) return 10
  return 100
}

async function loadSettings() {
  loading.value = true
  try {
    const res = await getSettings()
    groupedSettings.value = res.settings || {}
    // 初始化 RAG_HYBRID_WEIGHTS 双滑块
    for (const items of Object.values(groupedSettings.value)) {
      for (const item of items) {
        if (item.key === 'RAG_HYBRID_WEIGHTS') {
          initHybridWeights(item)
        }
      }
    }
  } catch (error: any) {
    ElMessage.error('加载配置失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

async function handleUpdate(item: SettingItem, value: any) {
  try {
    await updateSetting(item.key, value)
    // 更新本地状态
    item.current_value = value
    item.is_modified = (value !== item.default_value)
    ElMessage.success(`${item.desc} 已更新为 ${value}`)
  } catch (error: any) {
    ElMessage.error('更新失败: ' + (error.message || '未知错误'))
    // 回滚本地状态
    loadSettings()
  }
}

async function handleReset(item: SettingItem) {
  try {
    await resetSetting(item.key)
    item.current_value = item.default_value
    item.is_modified = false
    // RAG_HYBRID_WEIGHTS 重置时同步双滑块
    if (item.key === 'RAG_HYBRID_WEIGHTS') {
      initHybridWeights(item)
    }
    ElMessage.success(`${item.desc} 已重置为默认值`)
  } catch (error: any) {
    ElMessage.error('重置失败: ' + (error.message || '未知错误'))
  }
}

async function handleResetAll() {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有配置为默认值吗？此操作不可撤销。',
      '重置确认',
      { confirmButtonText: '确定重置', cancelButtonText: '取消', type: 'warning' }
    )
    await resetAllSettings()
    ElMessage.success('所有配置已重置为默认值')
    loadSettings()
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  loadSettings()
  loadEmbeddingProvider()
})
</script>

<style scoped>@import '../styles/settings-page.css';</style>
