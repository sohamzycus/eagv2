import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';
import path from 'path';

export default defineConfig({
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        service_worker: path.resolve(__dirname, 'src/background/service_worker.ts'),
        contentScript: path.resolve(__dirname, 'src/content/contentScript.ts'),
        overlay: path.resolve(__dirname, 'src/content/overlay/overlay.ts'),
        popup: path.resolve(__dirname, 'src/popup/popup.ts'),
        options: path.resolve(__dirname, 'src/options/options.ts'),
      },
      output: {
        entryFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId;
          if (facadeModuleId?.includes('service_worker')) {
            return 'background/service_worker.js';
          } else if (facadeModuleId?.includes('contentScript')) {
            return 'content/contentScript.js';
          } else if (facadeModuleId?.includes('overlay')) {
            return 'content/overlay/overlay.js';
          } else if (facadeModuleId?.includes('popup')) {
            return 'popup/popup.js';
          } else if (facadeModuleId?.includes('options')) {
            return 'options/options.js';
          }
          return '[name].js';
        },
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    target: 'es2020',
    minify: false, // Keep readable for debugging
  },
  plugins: [
    viteStaticCopy({
      targets: [
        // Copy manifest
        {
          src: 'src/manifest.json',
          dest: '.',
        },
        // Copy assets
        {
          src: 'assets/*',
          dest: 'assets',
        },
        // Copy HTML files
        {
          src: 'src/popup/popup.html',
          dest: 'popup',
        },
        {
          src: 'src/popup/popup.css',
          dest: 'popup',
        },
        {
          src: 'src/options/options.html',
          dest: 'options',
        },
        {
          src: 'src/options/options.css',
          dest: 'options',
        },
        {
          src: 'src/content/overlay/overlay.html',
          dest: 'content/overlay',
        },
        {
          src: 'src/content/overlay/overlay.css',
          dest: 'content/overlay',
        },
      ],
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
});
