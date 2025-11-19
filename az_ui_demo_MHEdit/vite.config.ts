import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Infer repo name when running inside GitHub Actions so Pages serves assets from /<repo>/
const repository = process.env.GITHUB_REPOSITORY
const repoName = repository ? repository.split('/').pop() : ''
const basePath = repoName ? `/${repoName}/` : '/'

export default defineConfig({
  plugins: [react()],
  base: basePath,
})
