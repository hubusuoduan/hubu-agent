<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h2>知识库管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建知识库
      </el-button>
    </div>

    <!-- 知识库列表 -->
    <div class="knowledge-list">
      <el-card v-for="kb in knowledgeList" :key="kb.id" class="knowledge-card">
        <div class="card-header">
          <div class="card-title">
            <el-icon :size="24" color="#09b572"><FolderOpened /></el-icon>
            <h3>{{ kb.name }}</h3>
          </div>
          <el-button type="danger" size="small" @click="handleDelete(kb.id)">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
        
        <p class="card-description">{{ kb.description || '暂无描述' }}</p>
        
        <!-- 上传文件区域 -->
        <div class="upload-area">
          <el-upload
            :action="`/api/v1/knowledge/upload?knowledge_id=${kb.id}`"
            :headers="uploadHeaders"
            :on-success="(res) => handleUploadSuccess(res, kb.id)"
            :on-error="handleUploadError"
            :before-upload="beforeUpload"
            :show-file-list="false"
          >
            <el-button size="small" type="success">
              <el-icon><Upload /></el-icon>
              上传文件
            </el-button>
          </el-upload>
          <span class="upload-tip">支持 .txt, .pdf, .docx, .md 等格式</span>
        </div>
      </el-card>

      <el-empty v-if="knowledgeList.length === 0" description="暂无知识库，请先创建" />
    </div>

    <!-- 创建知识库对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建知识库"
      width="500px"
    >
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入知识库描述（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Upload, FolderOpened } from '@element-plus/icons-vue'
import {
  createKnowledge,
  getKnowledgeList,
  deleteKnowledge,
  type Knowledge
} from '../apis/knowledge'

const knowledgeList = ref<Knowledge[]>([])
const showCreateDialog = ref(false)
const creating = ref(false)

const createForm = ref({
  name: '',
  description: ''
})

// 上传请求头（动态获取token，避免token刷新后仍使用旧token）
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`
}))

// 加载知识库列表
async function loadKnowledgeList() {
  try {
    const response = await getKnowledgeList(0, 100)
    knowledgeList.value = response.items
  } catch (error) {
    ElMessage.error('加载知识库列表失败')
    console.error(error)
  }
}

// 创建知识库
async function handleCreate() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }

  creating.value = true
  try {
    await createKnowledge(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.value = { name: '', description: '' }
    await loadKnowledgeList()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

// 删除知识库
async function handleDelete(knowledgeId: string) {
  try {
    await ElMessageBox.confirm('确定要删除该知识库吗？此操作不可恢复。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteKnowledge(knowledgeId)
    ElMessage.success('删除成功')
    await loadKnowledgeList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 上传前检查
function beforeUpload(file: File) {
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  const isValidType = ['.txt', '.pdf', '.docx', '.md', '.json', '.csv'].includes(ext)

  if (!isValidType) {
    ElMessage.error('只支持 .txt, .pdf, .docx, .md, .json, .csv 格式的文件')
    return false
  }

  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }

  return true
}

// 上传成功
function handleUploadSuccess(response: any, knowledgeId: string) {
  ElMessage.success('文件上传成功')
}

// 上传失败
function handleUploadError(error: any) {
  ElMessage.error('文件上传失败')
  console.error(error)
}

onMounted(() => {
  loadKnowledgeList()
})
</script>

<style scoped>
.knowledge-page {
  padding: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  color: #1f2937;
  font-weight: 700;
}

.knowledge-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.knowledge-card {
  transition: all 0.2s ease;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
}

.knowledge-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: rgba(99, 102, 241, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-title h3 {
  margin: 0;
  font-size: 17px;
  color: #1f2937;
  font-weight: 600;
}

.card-description {
  color: #6b7280;
  font-size: 14px;
  margin: 12px 0;
  min-height: 40px;
}

.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.upload-tip {
  font-size: 12px;
  color: #9ca3af;
}
</style>
