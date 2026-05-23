<template>
  <div class="login-page">
    <div class="login-container">
      <h2>用户登录</h2>
      <el-form :model="loginForm" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item>
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            @click="handleLogin"
            :loading="loading"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>
        
        <div class="register-link">
          还没有账号? <router-link to="/register">立即注册</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../apis/request'

const router = useRouter()
const loading = ref(false)

const loginForm = ref({
  username: '',
  password: ''
})

async function handleLogin() {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    const response = await request.post('/auth/login', loginForm.value)
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #1a1d23;
  position: relative;
  overflow: hidden;
}

.login-page::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(ellipse at 30% 50%, rgba(9, 181, 114, 0.12) 0%, transparent 50%),
              radial-gradient(ellipse at 70% 50%, rgba(9, 181, 114, 0.06) 0%, transparent 50%);
  animation: loginBgPulse 8s ease-in-out infinite alternate;
}

@keyframes loginBgPulse {
  0% { transform: scale(1) rotate(0deg); }
  100% { transform: scale(1.1) rotate(3deg); }
}

.login-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  padding: 48px 40px;
  border-radius: 20px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3);
  width: 400px;
  position: relative;
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.login-container h2 {
  text-align: center;
  margin-bottom: 36px;
  color: #1f2937;
  font-size: 24px;
  font-weight: 700;
}

.register-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #6b7280;
}

.register-link a {
  color: #09b572;
  text-decoration: none;
  font-weight: 500;
}

.register-link a:hover {
  color: #07a065;
}
</style>
