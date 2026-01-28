export const DEMO_MODE = false

// 后端API基础URL（用于window.open等直接导航）
export const API_BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000'
  : window.location.origin

