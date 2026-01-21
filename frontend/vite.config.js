import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,            // Escuchar en todas las IPs del contenedor
    port: 5173,
    watch: {
      usePolling: true,    // Obligatorio para que Docker detecte cambios en archivos
    },
  },
})
