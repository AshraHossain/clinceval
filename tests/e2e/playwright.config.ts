import { defineConfig } from '@playwright/test';
import * as path from 'path';

export default defineConfig({
  testDir: '.',
  use: { baseURL: 'http://localhost:8000' },
  webServer: {
    command: '.venv/bin/python -m uvicorn app.server:app --port 8000',
    cwd: path.resolve(__dirname, '../..'),
    url: 'http://localhost:8000',
    reuseExistingServer: true,
    timeout: 120_000, // first boot loads the embedding model
  },
});
