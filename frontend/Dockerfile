# ── 阶段 1: 构建前端 ──
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# ── 阶段 2: Nginx 托管 ──
# 1.31.9 includes the November 2026 HTTP/2, resolver and TLS security fixes.
FROM nginx:1.31.9-alpine

# 移除默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/radiomanager.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
