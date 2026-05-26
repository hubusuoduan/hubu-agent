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

const loading = ref(false)
const groupedSettings = ref<GroupedSettings>({})

const groupIconMap: Record<string, string> = {
  '对话历史': '💬',
  '上下文控制': '📏',
  'RAG检索': '🔍',
  '长期记忆': '🧠',
  'Agent': '🤖',
  '代码执行': '💻',
  'LLM': '🌐',
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
})
</script>

<style scoped>@import '../styles/settings-page.css';</style>
