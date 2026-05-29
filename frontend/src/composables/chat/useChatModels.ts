import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getModelList, enableProvider } from '../../apis/model'
import type { ProviderInfo } from '../../apis/model'

export function useChatModels() {
  const modelList = ref<ProviderInfo[]>([])

  async function loadModels() {
    try {
      const result = await getModelList()
      modelList.value = result.models
    } catch (e) {
      console.error('加载模型列表失败:', e)
    }
  }

  async function handleSwitchModel(providerId: number) {
    try {
      const result = await enableProvider(providerId)
      // 更新本地列表状态
      modelList.value.forEach(p => p.enable = p.id === providerId)
      ElMessage.success(`已切换到模型: ${result.provider.model}`)
    } catch (e: any) {
      ElMessage.error(e.message || '切换模型失败')
    }
  }

  return {
    modelList,
    loadModels,
    handleSwitchModel,
  }
}
