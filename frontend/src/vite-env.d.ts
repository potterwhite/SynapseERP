/// <reference types="vite/client" />

// Build-time constant injected by vite.config.ts → define.__APP_VERSION__
// Single source of truth: read from backend/src/synapse/__init__.py at build time.
declare const __APP_VERSION__: string
