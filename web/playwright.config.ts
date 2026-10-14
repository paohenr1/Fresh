import {defineConfig} from '@playwright/test';
export default defineConfig({
  testDir:'./tests', workers:1, fullyParallel:false,
  use:{baseURL:'http://127.0.0.1:5173',channel:process.env.CI ? undefined : 'msedge'},
  webServer:{command:'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort',
    url:'http://127.0.0.1:5173',reuseExistingServer:!process.env.CI},
});
