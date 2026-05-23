
<template>
  <el-dialog
    v-model="visible"
    title="导出对话"
    width="480px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form label-width="100px" label-position="left">
      <!-- 导出范围 -->
      <el-form-item label="导出范围">
        <el-select v-model="form.range" style="width: 100%">
          <el-option label="全部消息" value="all" />
          <el-option label="最近N条消息" value="recent" />
          <el-option label="自定义范围" value="custom" />
        </el-select>
      </el-form-item>

      <!-- 最近N条 -->
      <el-form-item v-if="form.range === 'recent'" label="消息条数">
        <el-input-number
          v-model="form.recent_count"
          :min="1"
          :max="9999"
          :step="10"
          style="width: 100%"
        />
      </el-form-item>

      <!-- 自定义范围 -->
      <template v-if="form.range === 'custom'">
        <el-form-item label="起始位置">
          <el-input-number
            v-model="form.start_index"
            :min="0"
            :max="9999"
            style="width: 100%"
            placeholder="从0开始"
          />
        </el-form-item>
        <el-form-item label="结束位置">
          <el-input-number
            v-model="form.end_index"
            :min="0"
            :max="9999"
            style="width: 100%"
            placeholder="不包含此位置"
          />
        </el-form-item>
      </template>

    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="exporting"
          @click="handleExport"
        >
          <el-icon v-if="!exporting"><Download /></el-icon>
          {{ exporting ? '导出中...' : '导出' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { exportDialog } from '../apis/export'
import type { ExportRange } from '../apis/export'

interface ExportForm {
  format: 'markdown'
  range: ExportRange
  recent_count: number
  start_index: number
  end_index: number
}

const props = defineProps<{
  modelValue: boolean
  dialogId: string | null
  messageCount: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = ref(false)
const exporting = ref(false)

const form = reactive<ExportForm>({
  format: 'markdown',
  range: 'all',
  recent_count: 20,
  start_index: 0,
  end_index: 0
})

// 同步 visible 状态
watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

// 当对话框打开时，设置默认 end_index
watch(() => props.modelValue, (val) => {
  if (val) {
    form.end_index = props.messageCount
  }
})

function handleClose() {
  visible.value = false
}

async function handleExport() {
  if (!props.dialogId) {
    ElMessage.warning('请先选择一个对话')
    return
  }

  // 校验自定义范围
  if (form.range === 'custom') {
    if (form.start_index >= form.end_index) {
      ElMessage.warning('起始位置必须小于结束位置')
      return
    }
  }

  exporting.value = true
  try {
    await exportDialog(props.dialogId, {
      format: form.format,
      range: form.range,
      recent_count: form.range === 'recent' ? form.recent_count : undefined,
      start_index: form.range === 'custom' ? form.start_index : undefined,
      end_index: form.range === 'custom' ? form.end_index : undefined,
    })
    ElMessage.success('导出成功')
    handleClose()
  } catch (error: any) {
    ElMessage.error(error.message || '导出失败')
    console.error('导出失败:', error)
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
