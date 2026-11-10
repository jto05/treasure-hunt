import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        // without this, Flask sees the proxy's own loopback connection
        // as the client IP instead of the real device's -- breaks
        // ip_to_mac()-based team registration while testing via `vite dev`
        xfwd: true,
      },
    },
  },
})
