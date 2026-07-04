import { defineConfig } from '@playwright/test';
import * as path from 'path';

export default defineConfig({
  testDir: '.',
  use: { baseURL: 'http://localhost:8000' },
  webServer: {
    // CI sets PYTHON=python (no venv); locally we default to the project venv
    command: `${process.env.PYTHON ?? '.venv/bin/python'} -m uvicorn app.server:app --port 8000`,
    cwd: path.resolve(__dirname, '../..'),
    url: 'http://localhost:8000',
    reuseExistingServer: true,
    timeout: 120_000, // first boot loads the embedding model
  },
});
