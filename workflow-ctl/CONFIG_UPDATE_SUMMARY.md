# 配置统一化更新说明

## 📋 更新概述

将外部服务的 URL 和 API Key 统一管理到配置文件中，并为所有违禁词接口添加 API Key 认证。

## 🔧 更改内容

### 1. 新增统一配置文件

**文件**: `app/config.py`

```python
# 代理服务配置
PROXY_BASE_URL = "http://38.128.233.224:38834"
PROXY_API_KEY = "xuanfeng_sdfasdfsdfkkllli8i3"

# 违禁词服务配置
FORBIDDEN_WORDS_SERVICE_URL = PROXY_BASE_URL
FORBIDDEN_WORDS_API_KEY = PROXY_API_KEY

# 具体接口 URL
PROXY_LOGS_URL = f"{PROXY_BASE_URL}/v1/logs"
PROXY_STATS_URL = f"{PROXY_BASE_URL}/v1/stats"
FORBIDDEN_WORDS_URL = f"{PROXY_BASE_URL}/v1/forbidden-words"
```

### 2. 更新 `app/api/sensitive_word.py`

#### 更改前：
```python
FORBIDDEN_WORDS_SERVICE_URL = "http://38.128.233.224:38834"
PROXY_API_KEY = "xuanfeng_sdfasdfsdfkkllli8i3"

# 调用外部服务时没有 API Key 认证
response = await client.post(
    f"{FORBIDDEN_WORDS_SERVICE_URL}/v1/forbidden-words",
    json=request_data
)
```

#### 更改后：
```python
from app.config import FORBIDDEN_WORDS_URL, FORBIDDEN_WORDS_API_KEY

# 调用外部服务时添加 API Key 认证
response = await client.post(
    FORBIDDEN_WORDS_URL,
    headers={
        "Authorization": f"Bearer {FORBIDDEN_WORDS_API_KEY}",
        "Content-Type": "application/json"
    },
    json=request_data
)
```

**影响的接口**:
- ✅ `POST /api/sensitive-words/add` - 添加违禁词（需要内部 API Key + 外部服务认证）
- ✅ `DELETE /api/sensitive-words/delete` - 删除违禁词（需要内部 API Key + 外部服务认证）
- ✅ `GET /api/sensitive-words/list` - 获取违禁词列表（无需内部认证，但调用外部服务时需要认证）

### 3. 更新 `app/api/chat.py`

#### 更改前：
```python
PROXY_URL = "http://38.128.233.224:38834/v1/chat/completions"
PROXY_LOGS_URL = "http://38.128.233.224:38834/v1/logs"
PROXY_API_KEY = "xuanfeng_sdfasdfsdfkkllli8i3"
```

#### 更改后：
```python
from app.config import PROXY_BASE_URL, PROXY_API_KEY, PROXY_LOGS_URL

PROXY_URL = f"{PROXY_BASE_URL}/v1/chat/completions"
```

## 📊 配置对比

| 配置项 | 更改前 | 更改后 |
|--------|--------|--------|
| **配置位置** | 分散在各个文件中 | 统一在 `app/config.py` |
| **API Key 认证** | 部分接口缺失 | 所有外部调用都添加认证 |
| **维护性** | 需要修改多个文件 | 只需修改一个配置文件 |

## 🔐 认证层级说明

### 违禁词接口认证层级

1. **`POST /add` 和 `DELETE /delete`**
   - 第一层：内部 API Key 认证（`verify_api_key_dependency`）
   - 第二层：外部服务认证（`Bearer xuanfeng_sdfasdfsdfkkllli8i3`）

2. **`GET /list`**
   - 第一层：无需内部认证（公开接口）
   - 第二层：外部服务认证（`Bearer xuanfeng_sdfasdfsdfkkllli8i3`）

## ✅ 验证步骤

### 1. 测试添加违禁词（需要内部 API Key）

```bash
curl -X POST "http://localhost:8889/api/sensitive-words/add" \
  -H "Authorization: Bearer YOUR_INTERNAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"word": "测试词"}'
```

### 2. 测试获取违禁词列表（无需内部 API Key）

```bash
curl -X GET "http://localhost:8889/api/sensitive-words/list"
```

### 3. 测试删除违禁词（需要内部 API Key）

```bash
curl -X DELETE "http://localhost:8889/api/sensitive-words/delete" \
  -H "Authorization: Bearer YOUR_INTERNAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"word": "测试词"}'
```

## 🎯 优势

1. **统一管理**: 所有外部服务配置集中在一个文件
2. **易于维护**: 修改 URL 或 API Key 只需改一处
3. **安全性提升**: 所有外部调用都添加了认证
4. **代码清晰**: 减少了硬编码，提高可读性

## 📝 注意事项

- 重启服务后新配置才会生效
- 确保外部服务 `http://38.128.233.224:38834` 可访问
- API Key `xuanfeng_sdfasdfsdfkkllli8i3` 需要保密
- 后续如需修改配置，只需编辑 `app/config.py` 文件





