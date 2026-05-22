# Frontend Dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app

# Копируем package files
COPY package*.json ./
COPY tsconfig.json ./

# Установка зависимостей
RUN npm ci --legacy-peer-deps

# Копирование исходного кода
COPY public/ ./public/
COPY src/ ./src/

RUN npm run build 2>&1 || true
# Сборка приложения
RUN npm run build

# Production stage
FROM nginx:alpine

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копирование собранного приложения
COPY --from=builder /app/build /usr/share/nginx/html

# Порт
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]
