<template>
  <div class="register-page">
    <div class="register-container">
      <h2>用户注册</h2>
      <el-form :model="registerForm" @submit.prevent="handleRegister">
        <el-form-item>
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item>
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱"
            prefix-icon="Message"
            size="large"
          />
        </el-form-item>
        
        <el-form-item>
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请确认密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            @click="handleRegister"
            :loading="loading"
            style="width: 100%"
          >
            注册
          </el-button>
        </el-form-item>
        
        <div class="login-link">
          已有账号? <router-link to="/login">立即登录</router-link>
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

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

async function handleRegister() {
  if (!registerForm.value.username || !registerForm.value.email || !registerForm.value.password) {
    ElMessage.warning('请填写完整信息')
    return
  }

  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    ElMessage.warning('两次密码输入不一致')
    return
  }

  if (registerForm.value.password.length < 6) {
    ElMessage.warning('密码长度至少6位')
    return
  }

  loading.value = true
  try {
    await request.post('/auth/register', {
      username: registerForm.value.username,
      email: registerForm.value.email,
      password: registerForm.value.password
    })
    ElMessage.success('注册成功,请登录')
    router.push('/login')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #1a1d23;
  position: relative;
  overflow: hidden;
}

.register-page::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(ellipse at 70% 50%, rgba(9, 181, 114, 0.12) 0%, transparent 50%),
              radial-gradient(ellipse at 30% 50%, rgba(9, 181, 114, 0.06) 0%, transparent 50%);
  animation: registerBgPulse 8s ease-in-out infinite alternate;
}

@keyframes registerBgPulse {
  0% { transform: scale(1) rotate(0deg); }
  100% { transform: scale(1.1) rotate(-3deg); }
}

.register-container {
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

.register-container h2 {
  text-align: center;
  margin-bottom: 36px;
  color: #1f2937;
  font-size: 24px;
  font-weight: 700;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #6b7280;
}

.login-link a {
  color: #09b572;
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  color: #07a065;
}
</style>
