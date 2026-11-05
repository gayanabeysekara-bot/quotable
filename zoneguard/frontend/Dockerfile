FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:22-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG ZG_BACKEND_URL=http://api:8000
ENV ZG_BACKEND_URL=$ZG_BACKEND_URL
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN adduser -S -u 10001 zoneguard
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
USER zoneguard
EXPOSE 3000
CMD ["node", "server.js"]
