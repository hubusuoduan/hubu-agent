import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadFile } from '../../apis/chat'

export function useChatFiles() {
  const uploadedFiles = ref<Array<{ file: File; content: string }>>([])
  const uploadingFile = ref(false)

  const ALLOWED_EXTENSIONS = [
    '.txt', '.md', '.pdf', '.docx', '.html', '.htm',
    '.csv', '.json', '.xml', '.xlsx', '.pptx', '.rtf',
  ]

  async function handleFileChange(uploadFileItem: any) {
    if (!uploadFileItem.raw) return

    const fileExt = '.' + uploadFileItem.name.split('.').pop().toLowerCase()

    if (!ALLOWED_EXTENSIONS.includes(fileExt)) {
      ElMessage.error(`不支持的文件类型: ${fileExt}。支持: ${ALLOWED_EXTENSIONS.join(', ')}`)
      return
    }

    if (uploadedFiles.value.some(f => f.file.name === uploadFileItem.name)) {
      ElMessage.warning(`文件 "${uploadFileItem.name}" 已上传`)
      return
    }

    uploadingFile.value = true

    try {
      const result = await uploadFile(uploadFileItem.raw)
      uploadedFiles.value.push({ file: uploadFileItem.raw, content: result.content })
      ElMessage.success(`文件 "${uploadFileItem.name}" 上传成功`)
    } catch (error: any) {
      ElMessage.error(error.message || '文件上传失败')
      console.error(error)
    } finally {
      uploadingFile.value = false
    }
  }

  function clearFile() {
    uploadedFiles.value = []
  }

  function removeFile(index: number) {
    uploadedFiles.value.splice(index, 1)
  }

  return {
    uploadedFiles,
    uploadingFile,
    handleFileChange,
    clearFile,
    removeFile,
  }
}
