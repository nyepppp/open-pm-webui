#!/bin/bash
# Fix script for Open WebUI PM Workspace issues

echo "Starting fixes..."

# 1. Clear build cache
echo "Clearing build cache..."
rm -rf .svelte-kit
rm -rf node_modules/.vite

echo "Build cache cleared. Please restart the dev server with: npm run dev:fast"
