FROM node:18-alpine

WORKDIR /app

# Kopírovanie package.json
COPY frontend/package*.json ./
RUN npm ci

# Kopírovanie kódu
COPY frontend/ .

# Build
RUN npm run build

# Spustenie
CMD ["npm", "start"]
