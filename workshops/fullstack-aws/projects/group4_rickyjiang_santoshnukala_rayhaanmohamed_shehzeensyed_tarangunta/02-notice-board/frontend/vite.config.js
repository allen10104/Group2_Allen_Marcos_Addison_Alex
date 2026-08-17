/**
 * Vite build configuration.
 *
 * Kept at the default on purpose - the deployment story does not need more. Two things
 * worth knowing, because both bite during the AWS tiers:
 *
 * 1. ENV VARS ARE BAKED IN AT BUILD TIME, not read at runtime. `npm run build` inlines
 *    import.meta.env.VITE_API_URL as a string literal into the bundle. Pointing the
 *    site at a different API therefore means REBUILDING and re-uploading - re-running
 *    `aws s3 sync` alone changes nothing. This is why the GitHub Actions workflow sets
 *    VITE_API_URL as an env var on the build step rather than as a Lambda variable.
 *
 * 2. Only names starting with VITE_ are exposed to client code. That prefix rule is a
 *    safety feature: it stops an AWS secret in the shell environment from being
 *    silently compiled into a public JavaScript bundle.
 *
 * The build lands in dist/, which is what gets synced to S3.
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})
