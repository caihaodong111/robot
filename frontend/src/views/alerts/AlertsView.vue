<template>
  <div class="bi-shell">
    <el-card class="bi-card">
      <template #header>
        <div class="bi-header">
          <div class="bi-title">
            <span class="title-text">可视化 BI</span>
            <span class="title-sub">输入机器人名称（表名）后加载可视化界面</span>
          </div>
        </div>
      </template>

      <div class="bi-controls">
        <el-input
          v-model="robotName"
          placeholder="例如：as33_020rb_400"
          clearable
          @keyup.enter="handleLoad"
        >
          <template #prepend>机器人名称</template>
        </el-input>
        <el-button type="primary" :disabled="!robotName.trim()" @click="handleLoad">
          加载
        </el-button>
        <el-button :disabled="!robotName.trim()" @click="handleOpenNew">
          新窗口打开
        </el-button>
      </div>

      <div class="bi-content">
        <div v-if="!activeName" class="bi-empty">
          请输入机器人名称后加载 BI 可视化界面
        </div>
        <iframe
          v-else
          class="bi-frame"
          :src="biUrl"
          title="BI 可视化"
        ></iframe>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const robotName = ref('')
const activeName = ref('')

const biUrl = computed(() => {
  const name = activeName.value.trim()
  return name ? `/api/robots/bi/?table=${encodeURIComponent(name)}&embed=1` : ''
})

const handleLoad = () => {
  const name = robotName.value.trim()
  if (!name) return
  activeName.value = name
}

const handleOpenNew = () => {
  const name = robotName.value.trim()
  if (!name) return
  window.open(`/api/robots/bi/?table=${encodeURIComponent(name)}`, '_blank')
}
</script>

<style scoped>
.bi-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bi-card :deep(.el-card__header) {
  padding: 14px 18px;
}

.bi-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.bi-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-text {
  font-size: 16px;
  font-weight: 700;
  color: rgba(15, 23, 42, 0.9);
}

.title-sub {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
}

.bi-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.bi-controls :deep(.el-input) {
  max-width: 420px;
}

.bi-content {
  min-height: 560px;
  border: 1px dashed rgba(148, 163, 184, 0.5);
  border-radius: 12px;
  background: rgba(148, 163, 184, 0.06);
  overflow: hidden;
}

.bi-empty {
  height: 560px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(15, 23, 42, 0.55);
  font-size: 14px;
}

.bi-frame {
  width: 100%;
  height: 720px;
  border: none;
  background: #fff;
}
</style>
