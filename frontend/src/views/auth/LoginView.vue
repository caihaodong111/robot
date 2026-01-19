<template>
  <div class="grid-wrapper login-page">
    <div class="grid-background"></div>

    <header class="top-nav">
      <div class="brand">
        <el-icon class="brand-icon" :size="24"><Cpu /></el-icon>
        <span class="brand-text">RobotOps</span>
        <span class="brand-divider">|</span>
        <span class="brand-subtext">机器人技术管理平台</span>
      </div>

      <nav class="nav-links">
        <a href="#" class="nav-link">帮助文档</a>
      </nav>
    </header>

    <main class="login-container">
      <div class="hero-section">
        <div class="hero-badge">
          <span class="pulse-dot"></span>
          系统运行正常
        </div>
        <h1 class="hero-title">
          智能运维 <br />
          <span class="text-gradient">连接未来</span>
        </h1>
        <p class="hero-desc">
          面向机器人与边缘设备的新一代轻量级管理平台。<br />
          实时监控 · 远程控制 · 告警闭环 · 统一门户
        </p>
        
        <div class="hero-stats">
          <div class="stat-item">
            <div class="stat-value">99.9%</div>
            <div class="stat-label">在线率</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">< 1.2s</div>
            <div class="stat-label">低延迟</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">24/7</div>
            <div class="stat-label">自动巡检</div>
          </div>
        </div>
      </div>

      <div class="login-card-wrapper">
        <div class="login-card">
          <div class="login-header">
            <h3>欢迎回来</h3>
            <p>请登录您的账号以继续</p>
          </div>

          <el-form 
            ref="loginFormRef"
            :model="loginForm"
            :rules="rules"
            class="login-form"
            size="large"
          >
            <el-form-item prop="username">
              <el-input 
                v-model="loginForm.username" 
                placeholder="请输入用户名"
                :prefix-icon="User"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input 
                v-model="loginForm.password" 
                type="password" 
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <div class="form-options">
              <el-checkbox v-model="rememberMe">记住我</el-checkbox>
              <a href="#" class="forgot-password">忘记密码?</a>
            </div>

            <el-button 
              type="primary" 
              class="login-button" 
              :loading="loading"
              @click="handleLogin"
            >
              登录控制台
            </el-button>
          </el-form>

        </div>
      </div>
    </main>
    
    <footer class="simple-footer">
      © {{ new Date().getFullYear() }} RobotOps Platform. internal-tool-v2.1
    </footer>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Cpu, User, Lock, FullScreen, Key } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await userStore.login(loginForm.username, loginForm.password)
        ElMessage.success('登录成功，正在跳转...')
        // 模拟一点延迟感，提升体验
        setTimeout(() => {
          router.push('/dashboard')
        }, 600)
      } catch (error) {
        ElMessage.error(error.message || '登录失败，请检查用户名或密码')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.grid-wrapper {
  min-height: 100vh;
  width: 100%;
  position: relative;
  background: #f8fafc;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.grid-background {
  position: absolute;
  inset: 0;
  z-index: 0;
  background-image: 
    radial-gradient(at 0% 0%, rgba(37, 99, 235, 0.08) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(14, 165, 233, 0.08) 0px, transparent 50%);
  background-size: 100% 100%;
}

.grid-background::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: linear-gradient(#e2e8f0 1px, transparent 1px),
    linear-gradient(to right, #e2e8f0 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, #000 40%, transparent 100%);
  opacity: 0.6;
}

.top-nav {
  position: relative;
  z-index: 10;
  padding: 24px 48px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #0f172a;
}

.brand-icon {
  color: #2563eb;
  filter: drop-shadow(0 4px 6px rgba(37, 99, 235, 0.2));
}

.brand-text {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.brand-divider {
  color: #cbd5e1;
  font-weight: 300;
}

.brand-subtext {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s;
}

.nav-link:hover {
  color: #2563eb;
}

.login-container {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 80px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.hero-section {
  flex: 1;
  max-width: 600px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 99px;
  font-size: 13px;
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 24px;
  backdrop-filter: blur(4px);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.hero-title {
  font-size: 56px;
  line-height: 1.1;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 24px;
  letter-spacing: -1.5px;
}

.text-gradient {
  background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero-desc {
  font-size: 18px;
  line-height: 1.6;
  color: #475569;
  margin-bottom: 48px;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: #e2e8f0;
}

.login-card-wrapper {
  flex: 0 0 420px;
}

.login-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  padding: 40px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.05),
    0 20px 25px -5px rgba(0, 0, 0, 0.05),
    0 0 0 1px rgba(0,0,0,0.02);
}

.login-header {
  margin-bottom: 32px;
  text-align: center;
}

.login-header h3 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px;
}

.login-header p {
  color: #64748b;
  font-size: 14px;
}

.login-form :deep(.el-input__wrapper) {
  background: #f8fafc;
  box-shadow: none;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  height: 48px;
  transition: all 0.2s;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  background: #fff;
  border-color: #2563eb;
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.forgot-password {
  font-size: 14px;
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%);
  border: none;
  font-weight: 600;
  transition: transform 0.1s, box-shadow 0.2s;
}

.login-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px -4px rgba(37, 99, 235, 0.3);
}

.login-button:active {
  transform: translateY(0);
}

.login-footer {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.login-footer span {
  font-size: 13px;
  color: #64748b;
}

.other-methods {
  display: flex;
  gap: 12px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.icon-btn:hover {
  border-color: #cbd5e1;
  color: #0f172a;
  background: #f8fafc;
}

.simple-footer {
  text-align: center;
  padding: 24px;
  font-size: 12px;
  color: #94a3b8;
  position: relative;
  z-index: 1;
}

@media (max-width: 1024px) {
  .hero-title { font-size: 42px; }
  .login-container { gap: 40px; flex-direction: column; padding: 24px; }
  .hero-section { text-align: center; margin-top: 20px; }
  .hero-stats { justify-content: center; }
  .login-card-wrapper { width: 100%; max-width: 420px; }
  .top-nav { padding: 16px 24px; }
  .nav-links { display: none; }
}
</style>
