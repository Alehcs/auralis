import { defineConfig } from 'vite';
export default defineConfig({base:'./',server:{port:5184,strictPort:true},preview:{port:4184,strictPort:true},build:{target:'es2022',rollupOptions:{input:{probe:'index.html',phase5:'phase5/index.html',phase6:'phase6/index.html'}}}});
