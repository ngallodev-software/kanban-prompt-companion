import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: 4173
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"]
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  }
});
