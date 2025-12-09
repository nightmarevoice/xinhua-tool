# API 文档

## 概述

Admin Manage System 提供 RESTful API 接口，用于管理 API Key、流程配置、Prompt 配置和模型参数配置。

## 基础信息

- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

### 分页响应
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 10
}
```

### 错误响应
```json
{
  "success": false,
  "message": "错误信息"
}
```

## API Key 管理

### 获取 API Key 列表
- **URL**: `/apikeys`
- **方法**: `GET`
- **参数**:
  - `page`: 页码 (默认: 1)
  - `page_size`: 每页数量 (默认: 10, 最大: 100)
  - `search`: 搜索关键词 (可选)

### 获取单个 API Key
- **URL**: `/apikeys/{id}`
- **方法**: `GET`

### 创建 API Key
- **URL**: `/apikeys`
- **方法**: `POST`
- **请求体**:
```json
{
  "name": "API Key 名称",
  "description": "描述",
  "permissions": ["read", "write"],
  "expires_at": "2024-12-31T23:59:59"
}
```

### 更新 API Key
- **URL**: `/apikeys/{id}`
- **方法**: `PUT`
- **请求体**: 同创建，所有字段可选

### 删除 API Key
- **URL**: `/apikeys/{id}`
- **方法**: `DELETE`

## 流程配置

### 获取流程列表
- **URL**: `/workflows`
- **方法**: `GET`
- **参数**:
  - `page`: 页码
  - `page_size`: 每页数量
  - `search`: 搜索关键词
  - `type`: 流程类型 (`proprietary` 或 `proprietary_to_general`)

### 创建流程
- **URL**: `/workflows`
- **方法**: `POST`
- **请求体**:
```json
{
  "name": "流程名称",
  "description": "描述",
  "type": "proprietary",
  "config": {
    "proprietary_model": {
      "model_name": "model-name",
      "parameters": {"temperature": 0.7}
    },
    "general_model": {
      "model_name": "general-model",
      "parameters": {"max_tokens": 1000}
    }
  }
}
```

## Prompt 配置

### 获取 Prompt 列表
- **URL**: `/prompts`
- **方法**: `GET`
- **参数**:
  - `page`: 页码
  - `page_size`: 每页数量
  - `search`: 搜索关键词
  - `model_type`: 模型类型 (`proprietary` 或 `general`)

### 创建 Prompt
- **URL**: `/prompts`
- **方法**: `POST`
- **请求体**:
```json
{
  "title": "Prompt 标题",
  "content": "Prompt 内容",
  "model_type": "proprietary",
  "category": "分类",
  "tags": ["标签1", "标签2"]
}
```

## 模型参数配置

### 获取模型参数列表
- **URL**: `/model-parameters`
- **方法**: `GET`
- **参数**:
  - `page`: 页码
  - `page_size`: 每页数量
  - `search`: 搜索关键词
  - `model_type`: 模型类型 (`proprietary` 或 `general`)

### 创建模型参数
- **URL**: `/model-parameters`
- **方法**: `POST`
- **请求体**:
```json
{
  "name": "参数名称",
  "type": "number",
  "default_value": 0.7,
  "model_type": "proprietary",
  "description": "参数描述",
  "required": true,
  "validation": {
    "min": 0,
    "max": 1
  }
}
```
