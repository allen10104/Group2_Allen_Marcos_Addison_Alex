// Base React support for Vite (JSX, fast refresh, etc).
import react from '@vitejs/plugin-react'

// The Tailwind CSS plugin for Vite — lets Tailwind classes work without
// a separate PostCSS config file.
import tailwindcss from '@tailwindcss/vite'

// defineConfig gives you autocomplete/type-checking for the config object.
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  // Both plugins run together: React handles JSX, Tailwind handles styles.
  plugins: [react(), tailwindcss()],
})