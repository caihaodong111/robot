import fs from "node:fs";
import path from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const DEVOPS_BASE = "/devops-app/";

const rewriteStaticPathsPlugin = () => ({
  name: "rewrite-devops-static-paths",
  closeBundle() {
    const distDir = path.resolve("dist");
    const htmlFiles = [];
    const walk = (dir) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const nextPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          walk(nextPath);
          continue;
        }
        if (entry.isFile() && nextPath.toLowerCase().endsWith(".html")) {
          htmlFiles.push(nextPath);
        }
      }
    };

    if (!fs.existsSync(distDir)) return;
    walk(distDir);

    for (const filePath of htmlFiles) {
      const original = fs.readFileSync(filePath, "utf8");
      const rewritten = original.replace(/(["'(=])\/static\//g, `$1${DEVOPS_BASE}static/`);
      if (rewritten !== original) {
        fs.writeFileSync(filePath, rewritten, "utf8");
      }
    }
  },
});

export default defineConfig(({ command }) => ({
  base: command === "build" ? DEVOPS_BASE : "/",
  plugins: [vue(), rewriteStaticPathsPlugin()],
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
}));
