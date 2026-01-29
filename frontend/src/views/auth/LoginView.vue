<template>
  <div class="grid-wrapper login-page">
    <div class="grid-background"></div>
    <div class="light-gold"></div>

    <!-- 扫描光束 -->
    <div class="light-beam"></div>
    <div class="light-beam"></div>
    <div class="light-beam"></div>

    <!-- 浮动粒子 -->
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

/* 透视网格地面 - 增强版 */
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

/* 蓝色主光 - 增强版 */
.grid-background::after {
  content: '';
  position: absolute;
  width: 150%;
  height: 300px;
  background: radial-gradient(ellipse at center, rgba(0, 102, 255, 0.5) 0%, rgba(0, 204, 255, 0.2) 40%, transparent 70%);
  top: 20%;
  left: -25%;
  transform: rotate(-8deg);
  filter: blur(50px);
  mix-blend-mode: screen;
  animation: bluePulse 4s ease-in-out infinite alternate;
}

@keyframes bluePulse {
  0% { opacity: 0.5; transform: rotate(-8deg) scale(1); }
  100% { opacity: 0.8; transform: rotate(-8deg) scale(1.1); }
}

/* 橙金亮线 - 增强版 */
.light-gold {
  position: absolute;
  width: 150%;
  height: 80px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(255, 174, 0, 0.1) 20%,
    rgba(255, 174, 0, 0.8) 45%,
    rgba(0, 204, 255, 0.8) 55%,
    rgba(0, 204, 255, 0.1) 80%,
    transparent 100%
  );
  top: 50%;
  left: -25%;
  transform: rotate(-8deg);
  filter: blur(25px);
  mix-blend-mode: screen;
  animation: moveLight 6s ease-in-out infinite alternate;
  z-index: 5;
  pointer-events: none;
}

@keyframes moveLight {
  0% {
    transform: rotate(-8deg) translateX(-8%) translateY(0);
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
  100% {
    transform: rotate(-8deg) translateX(8%) translateY(5px);
    opacity: 0.6;
  }
}

/* 额外的光束效果 */
.light-beam {
  position: absolute;
  width: 3px;
  height: 100vh;
  background: linear-gradient(to bottom,
    transparent,
    rgba(0, 204, 255, 0.6) 30%,
    rgba(0, 204, 255, 0.8) 50%,
    rgba(0, 204, 255, 0.6) 70%,
    transparent
  );
  filter: blur(2px);
  z-index: 3;
  pointer-events: none;
  animation: beamScan 8s ease-in-out infinite;
}

.light-beam:nth-child(1) {
  left: 20%;
  animation-delay: 0s;
}

.light-beam:nth-child(2) {
  left: 50%;
  animation-delay: 2s;
}

.light-beam:nth-child(3) {
  left: 80%;
  animation-delay: 4s;
}

@keyframes beamScan {
  0%, 100% {
    opacity: 0;
    transform: translateX(-20px);
  }
  10%, 90% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.8;
    transform: translateX(20px);
  }
}

/* 粒子效果 */
.particles {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  overflow: hidden;
}

.particle {
  position: absolute;
  width: 2px;
  height: 2px;
  background: rgba(0, 204, 255, 0.8);
  border-radius: 50%;
  animation: particleFloat 15s linear infinite;
}

.particle:nth-child(1) { left: 10%; animation-delay: 0s; }
.particle:nth-child(2) { left: 25%; animation-delay: 2s; }
.particle:nth-child(3) { left: 40%; animation-delay: 4s; }
.particle:nth-child(4) { left: 55%; animation-delay: 6s; }
.particle:nth-child(5) { left: 70%; animation-delay: 8s; }
.particle:nth-child(6) { left: 85%; animation-delay: 10s; }
.particle:nth-child(7) { left: 15%; animation-delay: 12s; }
.particle:nth-child(8) { left: 60%; animation-delay: 14s; }

@keyframes particleFloat {
  0% {
    transform: translateY(100vh) scale(0);
    opacity: 0;
  }
  10% {
    opacity: 1;
    transform: translateY(90vh) scale(1);
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-10vh) scale(0);
    opacity: 0;
  }
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
  color: #fff;
}

.brand-icon {
  color: #0066ff;
  filter: drop-shadow(0 0 10px rgba(0, 102, 255, 0.6));
}

.brand-text {
  font-size: 22px;
  font-weight: 900;
  letter-spacing: 2px;
  background: linear-gradient(180deg, #FFFFFF 30%, #999999 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-divider {
  color: #444;
  font-weight: 300;
}

.brand-subtext {
  font-size: 13px;
  color: #888;
  font-weight: 500;
  letter-spacing: 1px;
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
  color: #888;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s;
}

.nav-link:hover {
  color: #00ccff;
  text-shadow: 0 0 10px rgba(0, 204, 255, 0.5);
}

.login-container {
  position: relative;
  z-index: 20;
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
  animation: heroSlideIn 1s ease-out;
}

@keyframes heroSlideIn {
  0% {
    opacity: 0;
    transform: translateX(-50px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: rgba(0, 102, 255, 0.15);
  border: 1px solid rgba(0, 204, 255, 0.3);
  border-radius: 99px;
  font-size: 12px;
  font-weight: 600;
  color: #00ccff;
  margin-bottom: 30px;
  backdrop-filter: blur(8px);
  text-transform: uppercase;
  letter-spacing: 2px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00ff88;
  box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.7);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(0, 255, 136, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 255, 136, 0); }
}

.hero-title {
  font-size: clamp(48px, 6vw, 72px);
  line-height: 1.1;
  font-weight: 800;
  margin: 0 0 20px;
  letter-spacing: 4px;
  text-transform: uppercase;
  background: linear-gradient(180deg, #FFFFFF 30%, #888888 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: titleGlow 3s ease-in-out infinite alternate;
}

@keyframes titleGlow {
  0% { filter: drop-shadow(0 0 10px rgba(0, 204, 255, 0.3)); }
  100% { filter: drop-shadow(0 0 25px rgba(0, 204, 255, 0.6)); }
}

.text-gradient {
  background: linear-gradient(135deg, #00ccff 0%, #0066ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: textShine 4s ease-in-out infinite;
}

@keyframes textShine {
  0%, 100% { filter: brightness(1); }
  50% { filter: brightness(1.3); }
}

.hero-desc {
  font-size: 16px;
  line-height: 1.8;
  color: #aaa;
  margin-bottom: 50px;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 40px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #00ccff 0%, #0066ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 1px;
}

.stat-label {
  font-size: 11px;
  color: #666;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.stat-divider {
  width: 1px;
  height: 50px;
  background: linear-gradient(to bottom, transparent, #333, transparent);
}

.login-card-wrapper {
  flex: 0 0 420px;
}

.login-card {
  background: rgba(10, 10, 15, 0.85);
  backdrop-filter: blur(30px);
  padding: 45px;
  border-radius: 20px;
  border: 1px solid rgba(0, 204, 255, 0.2);
  box-shadow:
    0 0 40px rgba(0, 102, 255, 0.1),
    0 20px 40px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  animation: cardFadeIn 0.8s ease-out;
  transition: all 0.3s ease;
}

.login-card:hover {
  border-color: rgba(0, 204, 255, 0.4);
  box-shadow:
    0 0 60px rgba(0, 102, 255, 0.2),
    0 20px 40px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

@keyframes cardFadeIn {
  0% {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.login-header {
  margin-bottom: 35px;
  text-align: center;
}

.login-header h3 {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 10px;
  letter-spacing: 1px;
}

.login-header p {
  color: #666;
  font-size: 13px;
  letter-spacing: 0.5px;
}

.login-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
  box-shadow: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 14px 18px;
  height: 52px;
  transition: all 0.3s;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 204, 255, 0.3);
  background: rgba(255, 255, 255, 0.05);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.05);
  border-color: #00ccff;
  box-shadow: 0 0 20px rgba(0, 204, 255, 0.15);
}

.login-form :deep(.el-input__inner) {
  color: #fff;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #555;
}

.login-form :deep(.el-input__prefix) {
  color: #666;
}

.login-form :deep(.el-input__prefix-inner) {
  color: #666;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.form-options :deep(.el-checkbox__label) {
  color: #888;
  font-size: 13px;
}

.form-options :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #0066ff;
  border-color: #0066ff;
}

.forgot-password {
  font-size: 13px;
  color: #00ccff;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
}

.forgot-password:hover {
  color: #00aadd;
  text-shadow: 0 0 10px rgba(0, 204, 255, 0.4);
}

.login-button {
  width: 100%;
  height: 52px;
  font-size: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #0066ff 0%, #00ccff 100%);
  border: none;
  font-weight: 600;
  letter-spacing: 1px;
  transition: all 0.3s;
  box-shadow: 0 4px 20px rgba(0, 102, 255, 0.3);
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 204, 255, 0.4);
}

.login-button:active {
  transform: translateY(0);
}

.login-footer {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.login-footer span {
  font-size: 13px;
  color: #666;
}

.other-methods {
  display: flex;
  gap: 12px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.icon-btn:hover {
  border-color: rgba(0, 204, 255, 0.3);
  color: #00ccff;
  background: rgba(0, 204, 255, 0.1);
}

.simple-footer {
  text-align: center;
  padding: 24px;
  font-size: 11px;
  color: #444;
  position: relative;
  z-index: 10;
  letter-spacing: 1px;
  text-transform: uppercase;
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
