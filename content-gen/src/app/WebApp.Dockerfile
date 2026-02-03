# ============================================
# Frontend Dockerfile
# Multi-stage build for Content Generation Frontend
# Combines: frontend (React/Vite) + frontend-server (Node.js proxy)
# ============================================

# ============================================
# Stage 1: Build the React frontend with Vite
# ============================================
FROM node:20-alpine AS frontend-build

WORKDIR /app

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build the frontend (outputs to ../static, but we're in /app so it goes to /static)
# Override outDir to keep it in the container context
RUN npm run build -- --outDir ./dist

# ============================================
# Stage 2: Production Node.js server
# ============================================
FROM node:20-alpine AS production

WORKDIR /app

# Copy frontend-server package files
COPY frontend-server/package*.json ./

# Install only production dependencies
RUN npm ci --only=production

# Copy the server code
COPY frontend-server/server.js ./

# Copy built frontend assets from stage 1
COPY --from=frontend-build /app/dist ./static

# Environment variables (can be overridden at runtime)
ENV PORT=8080
ENV NODE_ENV=production

# Expose the port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:' + (process.env.PORT || 8080) + '/', (r) => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

# Start the server
CMD ["node", "server.js"]
