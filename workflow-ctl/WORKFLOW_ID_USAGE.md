# Workflow ID 使用说明

## 功能概述

`/stream` 接口现在支持通过 `workflowId` 参数指定使用哪个 workflow 配置。

## API 接口

### POST `/stream`

**请求体：**

```json
{
  "user_message": "用户消息内容",
  "workflowId": "workflow的backend_id（可选）"
}
```

**参数说明：**

- `user_message` (必填): 用户的聊天消息
- `workflowId` (可选): workflow 的 `backend_id` 字段值
  - 如果提供且存在，使用对应的 workflow 配置
  - 如果提供但不存在，回退到使用第一条 workflow
  - 如果不提供，默认使用第一条 workflow

## 使用示例

### 示例 1：不指定 workflowId（使用默认）

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "user_message": "你好，请介绍一下自己"
  }'
```

**行为：** 使用数据库中第一条 workflow 配置

### 示例 2：指定 workflowId

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "user_message": "你好，请介绍一下自己",
    "workflowId": "b40ba437-47c5-4be7-b9f7-fcca5bf6580c"
  }'
```

**行为：** 使用 `backend_id` 为 `b40ba437-47c5-4be7-b9f7-fcca5bf6580c` 的 workflow 配置

### 示例 3：指定不存在的 workflowId

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "user_message": "你好，请介绍一下自己",
    "workflowId": "non-existent-id"
  }'
```

**行为：** 
1. 尝试查找 `backend_id=non-existent-id` 的 workflow
2. 未找到，记录警告日志
3. 回退到使用第一条 workflow 配置

## 当前数据库中的 Workflow

根据最新的数据库状态，目前有以下 workflow 可用：

| ID | Name | Type | Backend ID | External ID |
|----|------|------|------------|-------------|
| 9 | 专有模型->通用模型 | proprietary->general | b40ba437-47c5-4be7-b9f7-fcca5bf6580c | 115139452 |
| 11 | 专有模型流程 | proprietary | 80b557e3-9a80-44a2-a5f0-aeb8ffdb21a7 | 729212644 |

## 日志输出

接口会输出详细的日志信息：

```
收到用户消息: 你好，请介绍一下自己...
workflowId: b40ba437-47c5-4be7-b9f7-fcca5bf6580c
使用指定的 workflow: 专有模型->通用模型 (backend_id=b40ba437-47c5-4be7-b9f7-fcca5bf6580c)
Workflow 类型: proprietary->general
Workflow 名称: 专有模型->通用模型
```

或者（未找到时）：

```
收到用户消息: 你好，请介绍一下自己...
workflowId: non-existent-id
未找到 backend_id=non-existent-id 的 workflow，使用默认第一条
Workflow 类型: proprietary->general
Workflow 名称: 专有模型->通用模型
```

或者（未提供时）：

```
收到用户消息: 你好，请介绍一下自己...
workflowId: None
未提供 workflowId，使用默认第一条 workflow
Workflow 类型: proprietary->general
Workflow 名称: 专有模型->通用模型
```

## 前端集成示例

### JavaScript/TypeScript

```typescript
async function sendChatMessage(message: string, workflowId?: string) {
  const response = await fetch('http://localhost:8000/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'your-api-key'
    },
    body: JSON.stringify({
      user_message: message,
      ...(workflowId && { workflowId })  // 只在有值时添加
    })
  });
  
  // 处理 SSE 流式响应
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    console.log(chunk);
  }
}

// 使用默认 workflow
await sendChatMessage("你好");

// 使用指定 workflow
await sendChatMessage("你好", "b40ba437-47c5-4be7-b9f7-fcca5bf6580c");
```

### Python

```python
import requests

def send_chat_message(message: str, workflow_id: str = None):
    url = "http://localhost:8000/api/chat/stream"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "your-api-key"
    }
    
    payload = {"user_message": message}
    if workflow_id:
        payload["workflowId"] = workflow_id
    
    response = requests.post(url, json=payload, headers=headers, stream=True)
    
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))

# 使用默认 workflow
send_chat_message("你好")

# 使用指定 workflow
send_chat_message("你好", "b40ba437-47c5-4be7-b9f7-fcca5bf6580c")
```

## 注意事项

1. **Backend ID 格式**: `workflowId` 应该是 UUID 格式的字符串（例如：`b40ba437-47c5-4be7-b9f7-fcca5bf6580c`）
2. **容错机制**: 如果提供的 `workflowId` 不存在，系统会自动回退到第一条 workflow，不会报错
3. **向后兼容**: 不提供 `workflowId` 时，行为与之前完全一致
4. **日志记录**: 所有 workflow 选择操作都会记录详细日志，便于调试

## 测试建议

1. 测试不提供 `workflowId` 的情况
2. 测试提供有效 `workflowId` 的情况
3. 测试提供无效 `workflowId` 的情况
4. 检查日志输出是否符合预期





