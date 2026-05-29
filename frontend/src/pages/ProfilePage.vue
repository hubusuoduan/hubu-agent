<template>
  <div class="profile-page">
    <div class="profile-page-inner">
    <!-- 顶部 Banner -->
    <div class="profile-banner">
      <div class="banner-content">
        <div class="banner-info">
          <div class="banner-icon">
            <el-icon :size="28" color="#fff"><User /></el-icon>
          </div>
          <div class="banner-text">
            <h2>个人信息</h2>
            <p>管理你的账户信息与安全设置</p>
          </div>
        </div>
      </div>
    </div>

    <div class="profile-content">
      <!-- 基本信息 -->
      <div class="profile-card">
        <div class="card-title">基本信息</div>
        <el-form
          ref="profileFormRef"
          :model="profileForm"
          :rules="profileRules"
          label-width="80px"
          label-position="left"
          class="profile-form"
        >
          <el-form-item label="用户名">
            <el-input :model-value="userInfo.username" disabled />
          </el-form-item>
          <el-form-item label="昵称" prop="nickname">
            <el-input v-model="profileForm.nickname" placeholder="请输入昵称" maxlength="50" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="profileSaving" @click="handleSaveProfile">
              保存修改
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 修改密码 -->
      <div class="profile-card">
        <div class="card-title">修改密码</div>
        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="80px"
          label-position="left"
          class="profile-form"
        >
          <el-form-item label="旧密码" prop="old_password">
            <el-input
              v-model="passwordForm.old_password"
              type="password"
              show-password
              placeholder="请输入旧密码"
            />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input
              v-model="passwordForm.new_password"
              type="password"
              show-password
              placeholder="请输入新密码（至少6位）"
            />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirm_password">
            <el-input
              v-model="passwordForm.confirm_password"
              type="password"
              show-password
              placeholder="请再次输入新密码"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="passwordSaving" @click="handleChangePassword">
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { getUserInfo, updateProfile, changePassword } from '../apis/auth'

// 用户信息
const userInfo = reactive({
  username: '',
  email: '',
  nickname: '',
})

// 基本信息表单
const profileFormRef = ref<FormInstance>()
const profileSaving = ref(false)
const profileForm = reactive({
  nickname: '',
  email: '',
})

const profileRules: FormRules = {
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
}

// 修改密码表单
const passwordFormRef = ref<FormInstance>()
const passwordSaving = ref(false)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码长度为6-128个字符', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

// 加载用户信息
async function loadUserInfo() {
  try {
    const data = await getUserInfo()
    userInfo.username = data.username
    userInfo.email = data.email || ''
    userInfo.nickname = data.nickname || ''
    profileForm.nickname = data.nickname || ''
    profileForm.email = data.email || ''
  } catch (e: any) {
    ElMessage.error(e.message || '获取用户信息失败')
  }
}

// 保存基本信息
async function handleSaveProfile() {
  if (!profileFormRef.value) return
  await profileFormRef.value.validate(async (valid) => {
    if (!valid) return
    profileSaving.value = true
    try {
      const data = await updateProfile({
        nickname: profileForm.nickname || undefined,
        email: profileForm.email || undefined,
      })
      userInfo.nickname = data.nickname || ''
      userInfo.email = data.email || ''
      ElMessage.success('个人信息更新成功')
    } catch (e: any) {
      ElMessage.error(e.message || '更新失败')
    } finally {
      profileSaving.value = false
    }
  })
}

// 修改密码
async function handleChangePassword() {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    passwordSaving.value = true
    try {
      await changePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
      })
      ElMessage.success('密码修改成功')
      // 清空表单
      passwordForm.old_password = ''
      passwordForm.new_password = ''
      passwordForm.confirm_password = ''
      passwordFormRef.value?.resetFields()
    } catch (e: any) {
      ElMessage.error(e.message || '修改密码失败')
    } finally {
      passwordSaving.value = false
    }
  })
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style>@import '../styles/profile-page.css';</style>
