# ============================================
# CMEP Web (Next.js) — self-contained multi-stage build.
#
# Build prebieha VNUTRI image (npm ci + npm run build), runtime bezi cez
# `next start`. Nevyzaduje `output: 'standalone'` — next.config.js ho
# zamerne NEMA (odstranene commitom 239011c, nekompatibilne s `next start`).
#
# PORT sa respektuje z prostredia (Render injektuje PORT), default 3001.
# ============================================

FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3001

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.js ./next.config.js
COPY --from=builder /app/public ./public

EXPOSE 3001

CMD ["sh", "-c", "exec node node_modules/next/dist/bin/next start --hostname 0.0.0.0 --port ${PORT:-3001}"]
