# 部署指南

## 环境要求

### 前端
- Node.js 16+ 
- npm 或 yarn

### 后端
- Python 3.8+
- pip

## 本地开发部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd admin-manage-system
```

### 2. 后端部署

#### 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 配置环境变量
```bash
cp env.example .env
# 编辑 .env 文件，配置数据库连接等
```

#### 初始化数据库
```bash
python init_db.py
```

#### 启动后端服务
```bash
python main.py
```

后端服务将在 `http://localhost:8888` 启动

### 3. 前端部署

#### 安装依赖
```bash
cd frontend
npm install
```

#### 启动前端服务
```bash
npm run dev
```

前端服务将在 `http://localhost:9000` 启动

## 生产环境部署

### 后端部署

#### 使用 Docker (推荐)

1. 创建 Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. 构建和运行:
```bash
docker build -t admin-manage-backend .
docker run -p 8000:8000 admin-manage-backend
```

#### 使用 Gunicorn
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 前端部署

#### 构建生产版本
```bash
cd frontend
npm run build
```

#### 使用 Nginx 部署
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 数据库配置

### MySQL (生产环境)
项目已配置为使用 MySQL 数据库。

#### 数据库连接信息
- **主机**: rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com
- **端口**: 3306
- **数据库**: xinhua_dev
- **用户名**: xuanfeng_dev
- **密码**: xuanfengkeji2025%

#### 连接字符串
```bash
DATABASE_URL=mysql+pymysql://xuanfeng_dev:xuanfengkeji2025%25@rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com:3306/xinhua_dev?charset=utf8mb4
```

### SQLite (开发环境)
如需使用 SQLite 进行本地开发，可以修改 `.env` 文件：
```bash
DATABASE_URL=sqlite:///./admin_manage.db
```

## 环境变量说明

### 后端环境变量
- `DATABASE_URL`: 数据库连接字符串 (已配置为 MySQL)
- `DB_HOST`: 数据库主机地址
- `DB_PORT`: 数据库端口
- `DB_NAME`: 数据库名称
- `DB_USER`: 数据库用户名
- `DB_PASSWORD`: 数据库密码
- `SECRET_KEY`: JWT 密钥
- `DEBUG`: 调试模式 (True/False)
- `ALLOWED_ORIGINS`: 允许的 CORS 源

### 前端环境变量
- `VITE_API_BASE_URL`: API 基础 URL (默认: /api)

## 监控和日志

### 日志配置
后端使用 Python logging 模块，可以配置日志级别和输出格式。

### 健康检查
访问 `http://localhost:8888/health` 检查服务状态。

## 故障排除

### 常见问题

1. **端口冲突**
   - 修改 `main.py` 中的端口号
   - 修改 `vite.config.ts` 中的端口号

2. **数据库连接失败**
   - 检查数据库服务是否启动
   - 验证连接字符串是否正确

3. **CORS 错误**
   - 检查 `main.py` 中的 CORS 配置
   - 确保前端 URL 在允许列表中

### 日志查看
```bash
# 后端日志
tail -f backend.log

# 前端构建日志
npm run build 2>&1 | tee build.log
```
