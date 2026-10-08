import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// During dev, proxy API calls to the FastAPI backend so the frontend can use
// relative `/api/...` URLs in every environment (dev, Docker, production).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Split the heavy chart/animation libs into their own chunks.
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          charts: ["recharts"],
          motion: ["framer-motion"],
        },
      },
    },
  },
});
