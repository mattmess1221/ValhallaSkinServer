import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: "../valhalla/dashboard/dist",
    manifest: true,
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: "src/main.ts",
      },
    },
  },
  base: "./",
  server: {
    origin: "http://localhost:5173",
    cors: {
      origin: "http://localhost:8000",
    },
  },
});
