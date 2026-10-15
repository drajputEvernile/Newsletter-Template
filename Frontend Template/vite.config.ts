import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 1001,
    strictPort: true,
    host: true,
    proxy: { "/api": "http://127.0.0.1:1002" },
  },
  preview: {
    port: 1001,
    strictPort: true,
  },
});
