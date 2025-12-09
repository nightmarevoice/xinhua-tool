# Workflow Control Service

工作流控制服务 - 提供 API Key 认证网关和配置存储功能

## 功能说明

### 1. 网关功能
所有调用该系统的接口都需要通过 API Key 认证。请求头中必须包含 `Authorization`，格式为：
- `Authorization: Bearer <api_key>`
- 或 `Authorization: ApiKey <api_key>`
- 或直接 `Authorization: <api_key>`

### 2. API Key 管理
提供完整的 API Key CRUD 接口，用于管理系统中的 API Key。

### 3. 流程配置存储
提供流程配置的存储和管理接口。

### 4. Prompt 配置存储
提供 Prompt 配置的存储和管理接口。

### 5. 模型参数配置存储
提供模型参数配置的存储和管理接口。

## 安装和启动

### 1. 安装依赖
```bash
cd workflow-ctl
pip install -r requirements.txt
```

### 2. 初始化数据库
```bash
python init_db.py
```

### 3. 启动服务
```bash
python main.py
```

服务将在 `http://localhost:8889` 启动

## API 端点

### 健康检查
- `GET /health` - 服务健康检查（无需认证）

### API Key 管理
- `GET /api/apikeys` - 获取 API Key 列表（无需认证）
- `POST /api/apikeys` - 创建 API Key（无需认证）
- `GET /api/apikeys/{id}` - 获取单个 API Key（无需认证）
- `PUT /api/apikeys/{id}` - 更新 API Key（无需认证）
- `DELETE /api/apikeys/{id}` - 删除 API Key（无需认证）

### 流程配置（需要认证）
- `GET /api/workflows` - 获取流程配置列表
- `POST /api/workflows` - 创建流程配置
- `GET /api/workflows/{id}` - 获取单个流程配置
- `PUT /api/workflows/{id}` - 更新流程配置
- `DELETE /api/workflows/{id}` - 删除流程配置

### Prompt 配置（需要认证）
- `GET /api/prompts` - 获取 Prompt 配置列表
- `POST /api/prompts` - 创建 Prompt 配置
- `GET /api/prompts/{id}` - 获取单个 Prompt 配置
- `PUT /api/prompts/{id}` - 更新 Prompt 配置
- `DELETE /api/prompts/{id}` - 删除 Prompt 配置

### 模型参数配置（需要认证）
- `GET /api/model-parameters` - 获取模型参数配置列表
- `POST /api/model-parameters` - 创建模型参数配置
- `GET /api/model-parameters/{id}` - 获取单个模型参数配置
- `PUT /api/model-parameters/{id}` - 更新模型参数配置
- `DELETE /api/model-parameters/{id}` - 删除模型参数配置

## 使用示例

### 创建 API Key
```bash
curl -X POST http://localhost:8889/api/apikeys \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Key",
    "description": "用于测试的 API Key",
    "key": "test-api-key-12345"
  }'
```

### 使用 API Key 访问受保护的接口
```bash
curl -X GET http://localhost:8889/api/workflows \
  -H "Authorization: Bearer test-api-key-12345"
```

## 项目结构

```
workflow-ctl/
├── app/
│   ├── api/              # API 路由
│   │   ├── apikey.py
│   │   ├── workflow.py
│   │   ├── prompt.py
│   │   └── model_parameter.py
│   ├── middleware/       # 中间件
│   │   └── auth.py
│   ├── models/           # 数据模型
│   ├── schemas/          # Pydantic 模型
│   ├── database/         # 数据库配置
│   └── storage/          # 存储相关
├── data/                 # 数据目录（SQLite 数据库）
├── main.py              # 主应用文件
├── init_db.py           # 数据库初始化
└── requirements.txt     # 依赖列表
```














