# 通用模型调用流程分析文档

## 📋 文档概述

本文档详细分析 `workflow-ctl/app/api/chat.py` 中**通用模型**的调用流程，包括两种调用场景：
1. **纯通用模型流程**（暂未实现）
2. **专有模型 → 通用模型流程**（已实现）

---

## 🏗️ 系统架构

### 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                     客户端请求                           │
│   POST /api/chat/stream                                 │
│   { user_message, workflowId }                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              workflow-ctl 服务                           │
│                                                          │
│  1. 验证 API Key                                         │
│  2. 查询 Workflow 配置                                   │
│  3. 查询 Prompts 提示词                                  │
│  4. 查询 LLM Providers 模型配置                          │
│  5. 根据 workflow_type 决定调用流程                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              外部 LLM 服务                               │
│   http://38.128.233.224:38834/v1/chat/completions        │
│   或其他配置的 api_base                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 数据模型

### 1. Workflow (流程配置)

**数据库表**: `workflows`

```python
class Workflow:
    id: int                    # 主键
    external_id: int           # backend 系统的 ID（哈希值）
    backend_id: str            # backend 系统的原始 UUID
    name: str                  # 流程名称
    description: str           # 流程描述
    workflow_type: str         # 流程类型 ⭐
    config: JSON               # 完整流程配置
    status: str                # active/inactive
    created_at: datetime
    updated_at: datetime
```

**workflow_type 类型**:
- `"proprietary"`: 纯专有模型流程
- `"proprietary->general"`: 专有模型 → 通用模型流程 ⭐

---

### 2. Prompt (提示词配置)

**数据库表**: `prompts`

```python
class Prompt:
    id: int                    # 主键
    external_id: int           # backend 系统的 ID
    title: str                 # 提示词标题
    system_prompt: str         # 系统提示词
    user_prompt: str           # 用户提示词模板
    model_type: str            # 模型类型 ⭐
    created_at: datetime
    updated_at: datetime
```

**model_type 类型**:
- `"proprietary"`: 专有模型提示词
- `"general"`: 通用模型提示词 ⭐

**user_prompt 模板变量**:
- `{user_message}`: 会被替换为用户输入的消息

---

### 3. LLMProvider (模型配置)

**数据库表**: `llm_providers`

```python
class LLMProvider:
    id: int                         # 主键
    external_id: int                # backend 系统的 ID
    name: str                       # 提供商名称
    provider: str                   # openai, azure, anthropic, custom 等
    api_key: str                    # API 密钥
    api_base: str                   # API 基础 URL ⭐
    api_version: str                # API 版本
    custom_config: JSON             # 自定义配置（如 temperature）
    default_model_name: str         # 默认模型名称 ⭐
    fast_default_model_name: str    # 快速模型名称
    deployment_name: str            # 部署名称
    default_vision_model: str       # 视觉模型
    model_configurations: JSON      # 模型配置数组
    category: str                   # 类别 ⭐
    is_default_provider: bool       # 是否为默认提供商
    is_default_vision_provider: bool
    created_at: datetime
    updated_at: datetime
```

**category 类型**:
- `"general"`: 通用模型 ⭐
- `"professional"`: 专有模型

**custom_config 示例**:
```json
{
  "temperature": "0.7",
  "max_tokens": "2000"
}
```

---

## 🔄 通用模型调用流程

### 场景 1: 纯通用模型流程（暂未实现）

**workflow_type**: `"general"`

**流程图**:
```
用户消息
   ↓
查询 Workflow (type="general")
   ↓
查询 Prompt (model_type="general")
   ↓
查询 LLMProvider (category="general")
   ↓
构建消息 (system_prompt + user_prompt)
   ↓
调用通用模型 (流式)
   ↓
返回 SSE 流式响应
```

**说明**: 目前代码中只实现了 `"proprietary"` 和 `"proprietary->general"` 两种类型，纯通用模型流程需要额外开发。

---

### 场景 2: 专有模型 → 通用模型流程（已实现）⭐

**workflow_type**: `"proprietary->general"`

这是**通用模型的主要调用场景**，分为两个步骤：

#### 📍 步骤 1: 调用专有模型（非流式）

```python
# 1. 获取专有模型配置
proprietary_prompt = prompts_dict.get("proprietary")
proprietary_provider = providers_dict.get("professional")

# 2. 构建消息
messages = []
if proprietary_prompt.system_prompt:
    messages.append({
        "role": "system", 
        "content": proprietary_prompt.system_prompt
    })
messages.append({
    "role": "user", 
    "content": proprietary_prompt.user_prompt.replace("{user_message}", user_message)
})

# 3. 调用专有模型（非流式）
proprietary_result = call_llm_non_stream(
    messages=messages,
    api_base=proprietary_provider.api_base,
    api_key=proprietary_provider.api_key,
    model=proprietary_provider.default_model_name,
    temperature=proprietary_temperature  # 从 custom_config 中提取
)
```

**请求示例**:
```http
POST http://38.128.233.224:38834/v1/chat/completions
Authorization: Bearer xuanfeng_sdfasdfsdfkkllli8i3
Content-Type: application/json

{
  "model": "qwen-plus",
  "messages": [
    {
      "role": "system",
      "content": "你是一个专业的新闻分析助手..."
    },
    {
      "role": "user",
      "content": "用户的原始消息"
    }
  ],
  "temperature": 0.7,
  "stream": false
}
```

**响应示例**:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "这是专有模型处理后的结果..."
      }
    }
  ]
}
```

---

#### 📍 步骤 2: 调用通用模型（流式）⭐

```python
# 1. 获取通用模型配置
general_prompt = prompts_dict.get("general")
general_provider = providers_dict.get("general")

# 2. 构建消息（使用专有模型的输出作为输入）
messages = []
if general_prompt.system_prompt:
    messages.append({
        "role": "system", 
        "content": general_prompt.system_prompt
    })
messages.append({
    "role": "user", 
    "content": general_prompt.user_prompt.replace("{user_message}", proprietary_result)
})

# 3. 调用通用模型（流式）
return StreamingResponse(
    stream_chat_response(
        messages=messages,
        api_base=general_provider.api_base,
        api_key=general_provider.api_key,
        model=general_provider.default_model_name,
        temperature=general_temperature  # 从 custom_config 中提取
    ),
    media_type="text/event-stream"
)
```

**关键点**:
- ✅ 专有模型的输出 (`proprietary_result`) 作为通用模型的输入
- ✅ 通用模型使用**流式调用**，实时返回内容
- ✅ 通用模型的 `user_prompt` 模板中的 `{user_message}` 被替换为专有模型的输出

**请求示例**:
```http
POST http://38.128.233.224:38834/v1/chat/completions
Authorization: Bearer xuanfeng_sdfasdfsdfkkllli8i3
Content-Type: application/json

{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "你是一个内容优化助手..."
    },
    {
      "role": "user",
      "content": "这是专有模型处理后的结果..."  ← 专有模型的输出
    }
  ],
  "temperature": 0.7,
  "stream": true
}
```

**流式响应示例**:
```
data: {"choices":[{"delta":{"content":"这"}}]}

data: {"choices":[{"delta":{"content":"是"}}]}

data: {"choices":[{"delta":{"content":"通用"}}]}

data: {"choices":[{"delta":{"content":"模型"}}]}

data: [DONE]
```

---

## 🔍 详细代码分析

### 核心函数: `stream_chat()`

**位置**: `workflow-ctl/app/api/chat.py:182-408`

#### 第一步: 获取 Workflow 配置

```python
if workflow_id:
    # 通过 backend_id 查找
    workflow = db.query(Workflow).filter(Workflow.backend_id == workflow_id).first()
    if not workflow:
        # 找不到则使用第一条
        workflow = db.query(Workflow).first()
else:
    # 未提供 workflowId，使用第一条
    workflow = db.query(Workflow).first()

workflow_type = workflow.workflow_type  # "proprietary->general"
```

---

#### 第二步: 获取 Prompts 提示词

```python
prompts = db.query(Prompt).all()
prompts_dict = {p.model_type: p for p in prompts}

# prompts_dict 结构:
# {
#   "proprietary": Prompt(model_type="proprietary", ...),
#   "general": Prompt(model_type="general", ...)  ← 通用模型提示词
# }
```

---

#### 第三步: 获取 LLM Providers 模型配置

```python
providers = db.query(LLMProvider).all()
providers_dict = {p.category: p for p in providers}

# providers_dict 结构:
# {
#   "professional": LLMProvider(category="professional", ...),
#   "general": LLMProvider(category="general", ...)  ← 通用模型配置
# }
```

---

#### 第四步: 根据 workflow_type 处理

```python
if workflow_type == "proprietary->general":
    # 1. 获取专有模型配置
    proprietary_prompt = prompts_dict.get("proprietary")
    proprietary_provider = providers_dict.get("professional")
    
    # 2. 获取通用模型配置 ⭐
    general_prompt = prompts_dict.get("general")
    general_provider = providers_dict.get("general")
    
    # 3. 调用专有模型（非流式）
    proprietary_result = call_llm_non_stream(...)
    
    # 4. 调用通用模型（流式）⭐
    return StreamingResponse(
        stream_chat_response(
            messages=[...],
            api_base=general_provider.api_base,
            api_key=general_provider.api_key,
            model=general_provider.default_model_name,
            temperature=general_temperature
        ),
        media_type="text/event-stream"
    )
```

---

### 通用模型流式调用函数: `stream_chat_response()`

**位置**: `workflow-ctl/app/api/chat.py:85-178`

```python
def stream_chat_response(
    messages: List[Dict[str, str]],
    api_base: str,              # general_provider.api_base
    api_key: str,               # general_provider.api_key
    model: str,                 # general_provider.default_model_name
    temperature: float = 0.7
):
    # 1. 发送开始事件
    yield generate_sse_event(
        {"type": "start", "message": "开始生成响应..."},
        event="start"
    )
    
    # 2. 构建请求体
    request_body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True  # 流式调用
    }
    
    # 3. 发送 HTTP 请求（流式）
    response = requests.post(
        f"{api_base}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json=request_body,
        stream=True,  # 启用流式响应
        timeout=None
    )
    
    # 4. 解析流式响应
    full_content = ""
    for line in response.iter_lines():
        if line:
            line_text = line.decode('utf-8')
            
            # 跳过 [DONE] 标记
            if line_text.strip() == "data: [DONE]":
                continue
            
            # 解析 SSE 格式：data: {...}
            if line_text.startswith("data: "):
                data_str = line_text[6:]
                data = json.loads(data_str)
                
                # 提取内容
                if "choices" in data:
                    delta = data["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    
                    if content:
                        full_content += content
                        # 发送内容块
                        yield generate_sse_event(
                            {"type": "content", "content": content},
                            event="message"
                        )
    
    # 5. 发送完成事件
    yield generate_sse_event(
        {"type": "done", "message": "响应生成完成", "full_content": full_content},
        event="done"
    )
```

---

## 📝 配置示例

### 通用模型 Prompt 配置示例

```json
{
  "id": 2,
  "external_id": 456,
  "title": "通用模型提示词",
  "system_prompt": "你是一个内容优化助手，负责将专业分析结果转化为易读的内容。",
  "user_prompt": "请优化以下内容：\n\n{user_message}",
  "model_type": "general"
}
```

**说明**:
- `model_type` 必须为 `"general"`
- `user_prompt` 中的 `{user_message}` 会被替换为专有模型的输出

---

### 通用模型 LLMProvider 配置示例

```json
{
  "id": 2,
  "external_id": 789,
  "name": "OpenAI GPT-4",
  "provider": "openai",
  "api_key": "sk-...",
  "api_base": "http://38.128.233.224:38834",
  "default_model_name": "gpt-4",
  "custom_config": {
    "temperature": "0.7",
    "max_tokens": "2000"
  },
  "category": "general",
  "is_default_provider": true
}
```

**说明**:
- `category` 必须为 `"general"`
- `api_base` 是通用模型的 API 端点
- `default_model_name` 是通用模型的名称（如 `gpt-4`, `gpt-3.5-turbo`）
- `custom_config.temperature` 控制生成的随机性

---

## 🔐 认证机制

### 两层认证

#### 1. workflow-ctl 层认证

```python
@router.post("/stream")
async def stream_chat(
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    # 验证客户端的 API Key
    pass
```

**客户端请求头**:
```http
Authorization: Bearer ak_5i_PjMh5bDSjWZN1xLnsLFj2NTV_G3DSwNy1Q01WNgE
```

---

#### 2. 外部 LLM 服务认证

```python
response = requests.post(
    f"{api_base}/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",  # 使用 general_provider.api_key
        "Content-Type": "application/json"
    },
    ...
)
```

**外部服务请求头**:
```http
Authorization: Bearer xuanfeng_sdfasdfsdfkkllli8i3
```

---

## 📊 完整调用流程图

```
┌──────────────────────────────────────────────────────────────────┐
│                        客户端发起请求                             │
│  POST /api/chat/stream                                           │
│  Authorization: Bearer ak_5i_PjMh5bDSjWZN1xLnsLFj2NTV_G3DSwNy... │
│  { "user_message": "分析这条新闻...", "workflowId": "uuid-123" } │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                   workflow-ctl 验证 API Key                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│              查询数据库获取配置                                    │
│  1. Workflow (workflow_type="proprietary->general")              │
│  2. Prompts (model_type="proprietary" & "general")               │
│  3. LLMProviders (category="professional" & "general")           │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                  步骤 1: 调用专有模型（非流式）                    │
│                                                                   │
│  POST http://38.128.233.224:38834/v1/chat/completions            │
│  Authorization: Bearer xuanfeng_sdfasdfsdfkkllli8i3              │
│  {                                                               │
│    "model": "qwen-plus",                                         │
│    "messages": [                                                 │
│      {"role": "system", "content": "专有模型系统提示词"},         │
│      {"role": "user", "content": "用户原始消息"}                  │
│    ],                                                            │
│    "temperature": 0.7,                                           │
│    "stream": false                                               │
│  }                                                               │
│                                                                   │
│  ← 返回: "这是专有模型处理后的结果..."                            │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│              步骤 2: 调用通用模型（流式）⭐                        │
│                                                                   │
│  POST http://38.128.233.224:38834/v1/chat/completions            │
│  Authorization: Bearer xuanfeng_sdfasdfsdfkkllli8i3              │
│  {                                                               │
│    "model": "gpt-4",                                             │
│    "messages": [                                                 │
│      {"role": "system", "content": "通用模型系统提示词"},         │
│      {"role": "user", "content": "这是专有模型处理后的结果..."}   │
│    ],                                                            │
│    "temperature": 0.7,                                           │
│    "stream": true                                                │
│  }                                                               │
│                                                                   │
│  ← 流式返回:                                                      │
│    data: {"choices":[{"delta":{"content":"这"}}]}                │
│    data: {"choices":[{"delta":{"content":"是"}}]}                │
│    data: {"choices":[{"delta":{"content":"通用"}}]}              │
│    data: {"choices":[{"delta":{"content":"模型"}}]}              │
│    ...                                                           │
│    data: [DONE]                                                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│              workflow-ctl 转换为 SSE 格式返回                     │
│                                                                   │
│  event: start                                                    │
│  data: {"type":"start","message":"开始生成响应..."}               │
│                                                                   │
│  event: message                                                  │
│  data: {"type":"content","content":"这"}                         │
│                                                                   │
│  event: message                                                  │
│  data: {"type":"content","content":"是"}                         │
│                                                                   │
│  ...                                                             │
│                                                                   │
│  event: done                                                     │
│  data: {"type":"done","message":"响应生成完成","full_content":"..."} │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      客户端接收流式响应                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 关键要点总结

### 通用模型的调用方式

1. **数据库配置**:
   - `Prompt.model_type = "general"` - 通用模型提示词
   - `LLMProvider.category = "general"` - 通用模型配置

2. **调用时机**:
   - 在 `workflow_type = "proprietary->general"` 流程中
   - 作为**第二步**，接收专有模型的输出

3. **输入来源**:
   - 专有模型的输出结果 (`proprietary_result`)
   - 通过 `user_prompt` 模板的 `{user_message}` 占位符传入

4. **调用方式**:
   - **流式调用** (`stream=True`)
   - 使用 `stream_chat_response()` 函数
   - 返回 SSE (Server-Sent Events) 格式

5. **配置参数**:
   - `api_base`: 通用模型的 API 端点
   - `api_key`: 通用模型的认证密钥
   - `model`: 通用模型名称（如 `gpt-4`）
   - `temperature`: 从 `custom_config` 中提取，默认 0.7

---

## 🔧 配置检查清单

要确保通用模型正常调用，需要检查以下配置：

### ✅ 数据库配置

- [ ] `prompts` 表中存在 `model_type="general"` 的记录
- [ ] `llm_providers` 表中存在 `category="general"` 的记录
- [ ] `workflows` 表中存在 `workflow_type="proprietary->general"` 的记录

### ✅ Prompt 配置

- [ ] `system_prompt` 已设置（可选）
- [ ] `user_prompt` 已设置且包含 `{user_message}` 占位符

### ✅ LLMProvider 配置

- [ ] `api_base` 已设置（如 `http://38.128.233.224:38834`）
- [ ] `api_key` 已设置
- [ ] `default_model_name` 已设置（如 `gpt-4`）
- [ ] `custom_config.temperature` 已设置（可选，默认 0.7）

### ✅ 网络配置

- [ ] workflow-ctl 服务可以访问 `api_base` 地址
- [ ] 防火墙允许出站连接
- [ ] API Key 有效且有足够的配额

---

## 🐛 常见问题排查

### 问题 1: 通用模型未被调用

**可能原因**:
- `workflow_type` 不是 `"proprietary->general"`
- 数据库中没有 `category="general"` 的 LLMProvider
- 数据库中没有 `model_type="general"` 的 Prompt

**排查方法**:
```sql
-- 检查 workflow 配置
SELECT id, name, workflow_type FROM workflows;

-- 检查 prompt 配置
SELECT id, title, model_type FROM prompts WHERE model_type = 'general';

-- 检查 provider 配置
SELECT id, name, category, default_model_name FROM llm_providers WHERE category = 'general';
```

---

### 问题 2: 通用模型返回错误

**可能原因**:
- `api_base` 配置错误
- `api_key` 无效或过期
- `default_model_name` 不存在
- 网络连接问题

**排查方法**:
```python
# 查看日志
logger.info(f"通用模型 - model: {general_provider.default_model_name}, temp: {general_temperature}")
logger.info(f"流式调用: {api_base}/chat/completions")
```

---

### 问题 3: 流式响应中断

**可能原因**:
- 超时设置过短
- 网络不稳定
- 外部服务限流

**排查方法**:
- 检查 `timeout` 设置（当前为 `None`，即无超时）
- 检查外部服务日志
- 检查网络连接稳定性

---

## 📚 相关文件

| 文件路径 | 说明 |
|---------|------|
| `workflow-ctl/app/api/chat.py` | 聊天接口主文件，包含通用模型调用逻辑 |
| `workflow-ctl/app/models/llm_provider.py` | LLMProvider 数据模型 |
| `workflow-ctl/app/models/prompt.py` | Prompt 数据模型 |
| `workflow-ctl/app/models/workflow.py` | Workflow 数据模型 |
| `workflow-ctl/app/schemas/llm_provider.py` | LLMProvider Schema |
| `workflow-ctl/app/schemas/prompt.py` | Prompt Schema |
| `workflow-ctl/app/config.py` | 统一配置文件 |

---

## 🎓 总结

通用模型在当前系统中的调用方式：

1. **触发条件**: `workflow_type = "proprietary->general"`
2. **调用位置**: 专有模型调用之后（第二步）
3. **输入数据**: 专有模型的输出结果
4. **调用方式**: 流式调用（SSE）
5. **配置来源**: 数据库中 `category="general"` 的 LLMProvider 和 `model_type="general"` 的 Prompt

**核心代码位置**: `workflow-ctl/app/api/chat.py:300-400`

---

**文档版本**: 1.0  
**最后更新**: 2025-11-27  
**作者**: AI Assistant




