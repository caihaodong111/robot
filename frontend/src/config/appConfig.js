export const DEMO_MODE = false

// 后端API基础URL（用于window.open等直接导航）
// 注意：不要在DEV环境硬编码localhost；当通过远程服务器访问前端时，
// 浏览器里的localhost会指向客户端本机，导致iframe/直链请求无法到达后端。
// 如需显式指定后端来源，可通过 VITE_API_BASE_URL 覆盖（例如 http://<server-ip>:8001）。
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin
