FROM node:24-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# The SSR build bundles its dependencies: no node_modules needed at runtime
FROM node:24-slim AS runtime
ENV NODE_ENV=production \
    PORT=4000 \
    CORE_API_URL=http://core:8000
WORKDIR /app
COPY --from=build --chown=node:node /app/dist/anonymizer-demo ./dist
USER node
EXPOSE 4000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "fetch('http://127.0.0.1:4000/').then((r) => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"
CMD ["node", "dist/server/server.mjs"]
