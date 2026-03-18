<template>
  <div class="devops-viewport">
    <div class="ambient-background">
      <div class="nebula blue"></div>
      <div class="nebula gold"></div>
      <div class="breathing-line gold-1"></div>
      <div class="breathing-line gold-2"></div>
      <div class="scan-grid"></div>
    </div>

    <div class="layout-wrapper">
      <header class="page-header entrance-slide-in">
        <div class="title-area">
          <h1 class="ios-title">TECHNICAL MANAGEMENT<span class="subtitle">技术管理</span></h1>
        </div>
      </header>

      <div class="devops-frame">
        <iframe
          ref="devopsFrame"
          class="devops-iframe"
          :src="frameUrl"
          title="Technical Management Embedded UI"
          loading="lazy"
          referrerpolicy="no-referrer"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

defineOptions({ name: 'DevOps' })

const devopsFrame = ref(null)
const baseUrl = import.meta.env.VITE_FRONTEND_VUE_URL || 'http://localhost:5174/'
const frameUrl = computed(() => {
  try {
    const url = new URL(baseUrl, window.location.origin)
    if (!url.searchParams.has('embed')) {
      url.searchParams.set('embed', '1')
    }
    return url.toString()
  } catch (error) {
    return baseUrl.includes('?') ? `${baseUrl}&embed=1` : `${baseUrl}?embed=1`
  }
})

const minFrameHeight = () => Math.max(window.innerHeight - 160, 600)

const handleFrameMessage = (event) => {
  if (!event?.data || event.data.type !== 'frontend-vue:height') return
  const nextHeight = Math.max(Number(event.data.height) || 0, minFrameHeight())
  if (devopsFrame.value) {
    devopsFrame.value.style.height = `${nextHeight}px`
  }
}

onMounted(() => {
  window.addEventListener('message', handleFrameMessage)
})

onBeforeUnmount(() => {
  window.removeEventListener('message', handleFrameMessage)
})
</script>

<style scoped>
.devops-viewport {
  background: #030508;
  min-height: 100vh;
  position: relative;
  overflow-y: auto;
  color: #fff;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

.ambient-background {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.nebula {
  position: absolute;
  width: 80vw;
  height: 70vh;
  filter: blur(120px);
  opacity: 0.28;
  mix-blend-mode: screen;
}

.nebula.blue {
  background: radial-gradient(circle, #0066ff, transparent 75%);
  top: -10%;
  left: -5%;
}

.nebula.gold {
  background: radial-gradient(circle, #ffaa00, transparent 75%);
  bottom: -10%;
  right: -5%;
}

.breathing-line {
  position: absolute;
  height: 1px;
  background: linear-gradient(90deg, transparent, #ffaa00, transparent);
  filter: blur(1px);
  opacity: 0.3;
  animation: breathe 8s infinite ease-in-out;
}

.gold-1 {
  width: 100%;
  top: 30%;
  left: -50%;
  transform: rotate(-5deg);
}

.gold-2 {
  width: 100%;
  bottom: 20%;
  right: -50%;
  transform: rotate(3deg);
  animation-delay: -4s;
}

.scan-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  mask-image: linear-gradient(to bottom, black, transparent);
  animation: gridMove 25s linear infinite;
}

@keyframes gridMove {
  from { background-position: 0 0; }
  to { background-position: 0 50px; }
}

@keyframes breathe {
  0%, 100% { opacity: 0.1; transform: scaleX(0.8) translateY(0); }
  50% { opacity: 0.5; transform: scaleX(1.2) translateY(-20px); }
}

.layout-wrapper {
  padding: 24px clamp(16px, 3vw, 48px);
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  min-height: 100vh;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.title-area {
  display: flex;
  flex-direction: column;
}

.ios-title {
  font-size: 32px;
  letter-spacing: -0.5px;
  background: linear-gradient(180deg, #fff 40%, rgba(255, 255, 255, 0.6));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 8px 0;
  position: relative;
  animation: titleGlow 2s ease-out forwards;
}

.ios-title .subtitle {
  font-size: 14px;
  color: #ffaa00;
  margin-left: 0;
  font-weight: 300;
  letter-spacing: 2px;
  display: block;
  margin-top: 4px;
}

@keyframes titleGlow {
  0% {
    text-shadow: 0 0 20px rgba(255, 170, 0, 0), 0 0 40px rgba(255, 170, 0, 0);
    filter: brightness(0.8);
  }
  50% {
    text-shadow: 0 0 20px rgba(255, 170, 0, 0.5), 0 0 40px rgba(255, 170, 0, 0.3);
    filter: brightness(1.2);
  }
  100% {
    text-shadow: 0 0 20px rgba(255, 170, 0, 0), 0 0 40px rgba(255, 170, 0, 0);
    filter: brightness(1);
  }
}

.devops-frame {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  overflow: hidden;
  min-height: calc(100vh - 160px);
  box-shadow: none;
}

.devops-iframe {
  width: 100%;
  height: 100%;
  min-height: calc(100vh - 160px);
  border: 0;
  display: block;
}

@media (max-width: 900px) {
  .devops-viewport {
    padding: 20px;
  }

  .devops-frame {
    height: calc(100vh - 180px);
  }
}
</style>
