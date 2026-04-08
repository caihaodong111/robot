import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    proxy: {
      "/api/robot/": {
        target: "http://172.16.17.244:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/robot\//, "/robot/"),
      },
      "/api/robot_test/": {
        target: "http://172.16.17.244:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/robot_test\//, "/robot_test/"),
      },
    },
  },
});
