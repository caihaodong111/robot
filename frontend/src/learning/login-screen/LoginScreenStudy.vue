<template>
  <div class="grid-wrapper login-page">
    <div class="grid-background"></div>
    <div class="light-gold"></div>

    <div class="light-beam"></div>
    <div class="light-beam"></div>
    <div class="light-beam"></div>

    <div class="particles">
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
    </div>

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
            <div class="stat-value">&lt; 1.2s</div>
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
import { ElMessage } from 'element-plus'
import { Cpu, User, Lock } from '@element-plus/icons-vue'

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

  await loginFormRef.value.validate((valid) => {
    if (!valid) return
    loading.value = true
    window.setTimeout(() => {
      loading.value = false
      ElMessage.success('学习版界面，仅保留视觉与交互效果')
    }, 600)
  })
}
</script>

<style scoped>
.grid-wrapper {
  min-height: 100vh;
  width: 100%;
  position: relative;
  background: #000;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.grid-background {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.grid-background::before {
  content: '';
  position: absolute;
  width: 200%;
  height: 200%;
  bottom: -30%;
  left: -50%;
  background-image:
    linear-gradient(to right, rgba(0, 204, 255, 0.15) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0, 204, 255, 0.15) 1px, transparent 1px);
  background-size: 60px 60px;
  transform: perspective(600px) rotateX(65deg);
  opacity: 0.6;
  animation: gridMove 20s linear infinite;
}

@keyframes gridMove {
  0% { background-position: 0 0; }
  100% { background-position: 0 60px; }
}

.grid-background::after {
  content: '';
  position: absolute;
  width: 150%;
  height: 300px;
  background: radial-gradient(ellipse at center, rgba(0, 102, 255, 0.5) 0%, rgba(0, 204, 255, 0.2) 40%, transparent 70%);
  top: 20%;
  left: -25%;
  filter: blur(60px);
  animation: pulseGlow 8s ease-in-out infinite alternate;
}

@keyframes pulseGlow {
  0% { opacity: 0.55; transform: translateY(0); }
  100% { opacity: 0.9; transform: translateY(20px); }
}

.light-gold {
  position: absolute;
  width: 500px;
  height: 500px;
  right: -150px;
  top: -100px;
  background: radial-gradient(circle, rgba(255, 174, 0, 0.18) 0%, transparent 70%);
  filter: blur(80px);
  animation: drift 12s ease-in-out infinite;
}

@keyframes drift {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-40px, 30px); }
}

.light-beam {
  position: absolute;
  top: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(to bottom, transparent, rgba(0, 204, 255, 0.4), transparent);
  box-shadow: 0 0 12px rgba(0, 204, 255, 0.35);
  animation: beamFloat 7s linear infinite;
}

.light-beam:nth-child(3) { left: 22%; animation-delay: 0s; }
.light-beam:nth-child(4) { left: 48%; animation-delay: 1.8s; }
.light-beam:nth-child(5) { left: 78%; animation-delay: 3.4s; }

@keyframes beamFloat {
  0% { opacity: 0.15; transform: translateY(-6%); }
  50% { opacity: 0.55; }
  100% { opacity: 0.15; transform: translateY(6%); }
}

.particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(0, 204, 255, 0.85);
  box-shadow: 0 0 14px rgba(0, 204, 255, 0.7);
  animation: particleFloat 10s linear infinite;
}

.particle:nth-child(1) { top: 18%; left: 12%; animation-delay: 0s; }
.particle:nth-child(2) { top: 32%; left: 28%; animation-delay: 1.2s; }
.particle:nth-child(3) { top: 62%; left: 18%; animation-delay: 2.4s; }
.particle:nth-child(4) { top: 26%; left: 62%; animation-delay: 3.6s; }
.particle:nth-child(5) { top: 70%; left: 54%; animation-delay: 4.8s; }
.particle:nth-child(6) { top: 40%; left: 82%; animation-delay: 6s; }
.particle:nth-child(7) { top: 76%; left: 74%; animation-delay: 7.2s; }
.particle:nth-child(8) { top: 54%; left: 90%; animation-delay: 8.4s; }

@keyframes particleFloat {
  0% { transform: translateY(0) scale(0.8); opacity: 0.2; }
  50% { transform: translateY(-24px) scale(1); opacity: 0.9; }
  100% { transform: translateY(-48px) scale(0.75); opacity: 0; }
}

.top-nav,
.login-container,
.simple-footer {
  position: relative;
  z-index: 1;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 40px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #f4f7fb;
}

.brand-icon {
  color: #00ccff;
  filter: drop-shadow(0 0 14px rgba(0, 204, 255, 0.5));
}

.brand-text {
  font-size: 20px;
  font-weight: 700;
}

.brand-divider,
.brand-subtext,
.nav-link {
  color: rgba(244, 247, 251, 0.66);
}

.nav-link {
  text-decoration: none;
}

.nav-link:hover {
  text-decoration: none;
}

.login-container {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(380px, 460px);
  gap: 48px;
  align-items: center;
  padding: 40px 56px 64px;
}

.hero-section {
  max-width: 760px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border: 1px solid rgba(0, 204, 255, 0.22);
  border-radius: 999px;
  background: rgba(8, 18, 32, 0.5);
  color: #dcecff;
  font-size: 14px;
  backdrop-filter: blur(20px);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2dff9f;
  box-shadow: 0 0 12px rgba(45, 255, 159, 0.8);
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.85; }
  50% { transform: scale(1.3); opacity: 1; }
}

.hero-title {
  margin: 28px 0 18px;
  font-size: clamp(56px, 6vw, 90px);
  line-height: 0.98;
  color: #f9fbff;
  letter-spacing: -0.05em;
}

.text-gradient {
  background: linear-gradient(90deg, #c4eeff 0%, #59c6ff 45%, #ffaa00 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-desc {
  margin: 0;
  font-size: 18px;
  line-height: 1.9;
  color: rgba(255, 255, 255, 0.72);
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 22px;
  margin-top: 40px;
}

.stat-item {
  min-width: 110px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  margin-top: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
}

.stat-divider {
  width: 1px;
  height: 42px;
  background: rgba(255, 255, 255, 0.12);
}

.login-card-wrapper {
  display: flex;
  justify-content: flex-end;
}

.login-card {
  width: 100%;
  padding: 28px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 28px;
  background: rgba(10, 16, 28, 0.72);
  backdrop-filter: blur(28px);
  box-shadow:
    0 24px 80px rgba(0, 0, 0, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.login-header h3 {
  margin: 0;
  font-size: 28px;
  color: #fff;
}

.login-header p {
  margin: 8px 0 0;
  color: rgba(255, 255, 255, 0.6);
}

.login-form {
  margin-top: 24px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 8px 0 22px;
  font-size: 13px;
}

.forgot-password {
  color: rgba(255, 255, 255, 0.62);
  text-decoration: none;
}

.forgot-password:hover {
  text-decoration: none;
}

.login-button {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(90deg, #0066ff 0%, #00ccff 100%);
  box-shadow: 0 14px 30px rgba(0, 102, 255, 0.3);
}

.simple-footer {
  padding: 18px 40px 28px;
  color: rgba(255, 255, 255, 0.38);
  font-size: 12px;
}

:deep(.el-input__wrapper) {
  min-height: 48px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

:deep(.el-input__inner) {
  color: #fff;
}

:deep(.el-checkbox) {
  color: rgba(255, 255, 255, 0.65);
}

@media (max-width: 1080px) {
  .login-container {
    grid-template-columns: 1fr;
    padding: 24px 24px 56px;
  }

  .login-card-wrapper {
    justify-content: flex-start;
  }
}

@media (max-width: 720px) {
  .top-nav {
    flex-direction: column;
    gap: 14px;
    align-items: flex-start;
    padding: 24px;
  }

  .hero-stats {
    flex-wrap: wrap;
    gap: 18px;
  }

  .stat-divider {
    display: none;
  }

  .login-card {
    padding: 22px;
  }

  .simple-footer {
    padding: 18px 24px 24px;
  }
}
</style>
