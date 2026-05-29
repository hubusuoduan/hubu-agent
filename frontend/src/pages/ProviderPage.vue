<template>
  <div class="provider-page">
    <div class="provider-page-inner">
      <!-- 顶部 Banner -->
      <div class="provider-banner">
        <div class="banner-content">
          <div class="banner-info">
            <div class="banner-icon">
              <el-icon :size="28" color="#fff"><Cpu /></el-icon>
            </div>
            <div class="banner-text">
              <h2>模型供应商</h2>
              <p>管理 LLM 模型供应商配置，启用后即可使用</p>
            </div>
          </div>
          <el-button @click="openCreateDialog" type="primary" size="large" round style="background: #0891b2; border-color: #0891b2;">
            <el-icon><Plus /></el-icon>
            添加供应商
          </el-button>
        </div>
      </div>

      <!-- Provider 列表 -->
      <div v-loading="loading" class="provider-content">
        <div v-if="providers.length === 0 && !loading" class="provider-empty">
          <el-empty description="暂无模型供应商配置">
            <el-button type="primary" @click="openCreateDialog">添加供应商</el-button>
          </el-empty>
        </div>

        <div v-else class="provider-list">
          <div
            v-for="provider in providers"
            :key="provider.id"
            :class="['provider-card', { active: provider.enable }]"
          >
            <div class="provider-header">
              <div class="provider-title">
                <el-icon :size="20" :color="provider.enable ? '#409eff' : '#909399'"><Cpu /></el-icon>
                <span class="provider-model">{{ provider.model }}</span>
                <el-tag v-if="provider.enable" type="success" size="small" effect="dark">使用中</el-tag>
              </div>
              <div class="provider-actions">
                <el-tooltip content="启用此模型" placement="top" :show-after="300">
                  <el-switch
                    :model-value="provider.enable"
                    @change="(val: any) => handleEnable(provider, val)"
                    :disabled="provider.enable"
                  />
                </el-tooltip>
                <el-button size="small" @click="openEditDialog(provider)">编辑</el-button>
                <el-button size="small" type="danger" plain @click="handleDelete(provider)">删除</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑供应商' : '添加供应商'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="模型名称" prop="model">
          <el-input v-model="form.model" placeholder="如 qwen-plus-2025-07-28、gpt-4o 等" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="form.api_key"
            :placeholder="isEditing ? '不修改请保持原值，修改请输入新的 API Key' : 'sk-xxx'"
            show-password
          />
        </el-form-item>
        <el-form-item label="Base URL" prop="base_url">
          <el-input v-model="form.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="立即启用">
          <el-switch v-model="form.enable" />
          <span class="form-hint">启用后将自动关闭其他供应商</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Cpu, Plus } from '@element-plus/icons-vue'
import {
  getProviderList,
  createProvider,
  updateProvider,
  deleteProvider,
  enableProvider,
  getProviderDetail,
  type ProviderInfo,
} from '../apis/model'

const loading = ref(false)
const providers = ref<ProviderInfo[]>([])

// 对话框
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref()

const form = ref({
  model: '',
  api_key: '',
  base_url: '',
  enable: false,
})

// 记住编辑时脱敏的 api_key，用于判断用户是否修改
const originalMaskedApiKey = ref('')

const formRules = {
  model: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }],
}

async function loadProviders() {
  loading.value = true
  try {
    const res = await getProviderList()
    providers.value = res.providers || []
  } catch (e: any) {
    ElMessage.error('加载供应商列表失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  form.value = { model: '', api_key: '', base_url: '', enable: false }
  dialogVisible.value = true
}

async function openEditDialog(provider: ProviderInfo) {
  isEditing.value = true
  editingId.value = provider.id
  // 从后端获取详情（脱敏 api_key + 完整 base_url）
  try {
    const detail = await getProviderDetail(provider.id)
    form.value = {
      model: detail.model,
      api_key: detail.api_key,  // 脱敏值，如 sk-****1234
      base_url: detail.base_url,
      enable: detail.enable,
    }
    // 记住脱敏值，提交时判断用户是否修改了 api_key
    originalMaskedApiKey.value = detail.api_key
  } catch (e: any) {
    ElMessage.error('获取供应商详情失败: ' + (e.message || '未知错误'))
    return
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (isEditing.value && editingId.value) {
      const data: Record<string, any> = { model: form.value.model }
      // api_key：如果用户没修改（仍是脱敏值），则不提交，保留原值
      if (form.value.api_key && form.value.api_key !== originalMaskedApiKey.value) {
        data.api_key = form.value.api_key
      }
      data.base_url = form.value.base_url
      await updateProvider(editingId.value, data)
      ElMessage.success('供应商已更新')
    } else {
      await createProvider(form.value)
      ElMessage.success('供应商已添加')
    }
    dialogVisible.value = false
    await loadProviders()
  } catch (e: any) {
    ElMessage.error((isEditing.value ? '更新' : '添加') + '失败: ' + (e.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

async function handleEnable(provider: ProviderInfo, val: boolean) {
  if (!val) return // 不允许手动关闭，只能切换到其他
  try {
    await enableProvider(provider.id)
    await loadProviders()
    ElMessage.success(`已切换到模型: ${provider.model}`)
  } catch (e: any) {
    ElMessage.error('切换失败: ' + (e.message || '未知错误'))
  }
}

async function handleDelete(provider: ProviderInfo) {
  try {
    await ElMessageBox.confirm(
      `确定删除供应商「${provider.model}」吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await deleteProvider(provider.id)
    ElMessage.success('已删除')
    await loadProviders()
  } catch {
    // 取消删除
  }
}

onMounted(loadProviders)
</script>

<style>
@import '../styles/provider-page.css';
</style>
