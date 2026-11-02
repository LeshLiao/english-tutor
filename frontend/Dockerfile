# 兩階段：node build → nginx 提供靜態檔並反向代理 /api/* 到 backend
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# 容器版不把 API key 放進 bundle；由 nginx 注入 X-API-Key
ENV VITE_API_KEY=
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# 官方映像會在啟動時用 envsubst 把 /etc/nginx/templates/*.template 轉成 conf.d/*.conf
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 80
