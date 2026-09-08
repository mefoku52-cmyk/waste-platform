FROM node:22-alpine

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3001
ENV HOSTNAME=0.0.0.0

COPY .next/standalone/ ./
COPY .next/static/ ./apps/web/.next/static/

EXPOSE 3001

CMD ["node", "server.js"]
