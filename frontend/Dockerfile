# 构建阶段
FROM node:18-slim AS builder

WORKDIR /app

# 配置 npm 使用国内镜像源（加速下载）
RUN npm config set registry https://registry.npmmirror.com && \
    npm config set sass_binary_site https://npmmirror.com/mirrors/node-sass && \
    npm config set phantomjs_cdnurl https://npmmirror.com/mirrors/phantomjs && \
    npm config set chromedriver_cdnurl https://npmmirror.com/mirrors/chromedriver && \
    npm config set electron_mirror https://npmmirror.com/mirrors/electron/ && \
    npm config set sharp_binary_host https://npmmirror.com/mirrors/sharp && \
    npm config set sharp_libvips_binary_host https://npmmirror.com/mirrors/sharp-libvips

# 配置 npm 网络参数（提高稳定性）
RUN npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set fetch-timeout 300000

# 复制 package.json（单独复制，利用 Docker 缓存）
COPY package.json .npmrc* ./

# 安装依赖（利用 BuildKit 缓存挂载，加速构建）
# --mount=type=cache 会在构建间保留 npm 缓存
RUN --mount=type=cache,target=/root/.npm \
    rm -f package-lock.json && \
    npm install --legacy-peer-deps --verbose || \
    (echo "首次安装失败，重试..." && sleep 5 && npm install --legacy-peer-deps --verbose)

# 复制源代码（代码变化不会影响依赖层缓存）
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物到 nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]

