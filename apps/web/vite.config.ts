import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import cesium from "vite-plugin-cesium";

export default defineConfig({
  plugins: [react(), cesium()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: { "/api": process.env.NEXUS_API_TARGET ?? "http://127.0.0.1:8000" },
  },
});
