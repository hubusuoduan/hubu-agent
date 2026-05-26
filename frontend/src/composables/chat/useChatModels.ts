import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getModelList, switchModel } from '../../apis/model'
import type { ModelInfo } from '../../apis/model'

export function useChatModels() {
  const modelList = ref<ModelInfo[]>([])
  const currentModelId = ref('')

  async function loadModels() {
    try {
      const result = await getModelList()
      modelList.value = result.models
      currentModelId.value = result.current
    } catch (e) {
      console.error('加载模型列表失败:', e)
    }
  }

  async function handleSwitchModel(providerId: string) {
    try {
      const result = await switchModel(providerId)
      currentModelId.value = providerId
      ElMessage.success(`已切换到模型: ${result.current.name}`)
    } catch (e: any) {
      ElMessage.error(e.message || '切换模型失败')
    }
  }

  return {
    modelList,
    currentModelId,
    loadModels,
    handleSwitchModel,
  }
}
