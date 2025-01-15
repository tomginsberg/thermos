import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
import { VitePWA } from 'vite-plugin-pwa'
// Import JSON file
import iconsData from './icons.json'

export default defineConfig({
  plugins: [react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Heat',
        short_name: 'Heat',
        start_url: '/',
        display: 'standalone',
        background_color: '#000000',
        theme_color: '#000000',
        // use the icons from iconsData
        icons: iconsData.icons
      }
    })
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
