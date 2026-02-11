import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // เปิดให้ Docker เข้าถึงได้
    port: 5173, 
    watch: {
      usePolling: true, // <--- จุดเปลี่ยนชีวิต! สั่งให้มันเช็คไฟล์ตลอดเวลา
    },
  },
})