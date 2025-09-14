import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';
import path from 'path';

export default defineConfig({
  plugins: [
    viteStaticCopy({
      targets: [
        {
          src: 'src/manifest.json',
          dest: '.'
        },
        {
          src: 'assets/*',
          dest: 'assets'
        },
        {
          src: 'src/popup/popup.html',
          dest: 'popup'
        },
        {
          src: 'src/popup/popup.css',
          dest: 'popup'
        },
        {
          src: 'src/options/options.html',
          dest: 'options'
        },
        {
          src: 'src/options/options.css',
          dest: 'options'
        },
        {
          src: 'src/content/overlay/overlay.html',
          dest: 'content/overlay'
        },
        {
          src: 'src/content/overlay/overlay.css',
          dest: 'content/overlay'
        }
      ]
    })
  ],
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        service_worker: path.resolve(__dirname, 'src/background/service_worker.ts'),
        contentScript: path.resolve(__dirname, 'src/content/contentScript.ts'),
        overlay: path.resolve(__dirname, 'src/content/overlay/overlay.ts'),
        popup: path.resolve(__dirname, 'src/popup/popup.ts'),
        options: path.resolve(__dirname, 'src/options/options.ts')
      },
      output: {
        entryFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId;
          if (facadeModuleId?.includes('service_worker')) {
            return 'background/service_worker.js';
          }
          if (facadeModuleId?.includes('contentScript')) {
            return 'content/contentScript.js';
          }
          if (facadeModuleId?.includes('overlay/overlay')) {
            return 'content/overlay/overlay.js';
          }
          if (facadeModuleId?.includes('popup')) {
            return 'popup/popup.js';
          }
          if (facadeModuleId?.includes('options')) {
            return 'options/options.js';
          }
          return '[name].js';
        },
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.html')) {
            if (assetInfo.name.includes('popup')) return 'popup/popup.html';
            if (assetInfo.name.includes('options')) return 'options/options.html';
            if (assetInfo.name.includes('overlay')) return 'content/overlay/overlay.html';
          }
          if (assetInfo.name?.endsWith('.css')) {
            if (assetInfo.name.includes('popup')) return 'popup/popup.css';
            if (assetInfo.name.includes('options')) return 'options/options.css';
            if (assetInfo.name.includes('overlay')) return 'content/overlay/overlay.css';
          }
          return 'assets/[name]-[hash][extname]';
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  }
});
