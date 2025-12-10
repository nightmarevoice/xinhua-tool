# API 密钥加密存储功能说明

## 概述

本系统实现了完整的API密钥加密存储和脱敏显示功能，确保敏感信息的安全性。

## 功能特性

### 1. 加密存储
- **存储方式**：所有API密钥在存储到数据库前都会被加密
- **加密算法**：使用 Fernet 对称加密（基于 AES-128-CBC）
- **密钥派生**：使用 PBKDF2 算法从配置的密钥派生加密密钥

### 2. 脱敏显示
- **显示格式**：`sk-****99iJ--goa2xynmofjg`
- **规则**：显示前3个字符 + `****` + 后12个字符
- **目的**：让用户能识别密钥但无法获取完整内容

### 3. 智能更新
- **保持原密钥**：编辑时如果不修改密钥字段，保持原加密状态
- **新密钥加密**：输入新密钥时自动加密存储
- **识别机制**：通过检查是否包含 `****` 判断是否为脱敏格式

### 4. 使用时解密
- **自动解密**：在调用LLM API时自动解密获取原始密钥
- **透明使用**：应用层无需关心加解密过程

## 技术实现

### Backend (后端服务)

#### 1. 加密工具 (`backend/app/utils/crypto.py`)

```python
# 加密API密钥
def encrypt_api_key(api_key: str) -> str:
    """将明文密钥加密为密文"""
    
# 解密API密钥
def decrypt_api_key(encrypted_key: str) -> str:
    """将密文解密为明文"""
    
# 脱敏显示
def mask_api_key(api_key: str) -> str:
    """返回脱敏格式：sk-****99iJ--goa2xynmofjg"""
    
# 判断是否加密
def is_encrypted(value: str) -> bool:
    """检查字符串是否已加密"""
```

#### 2. API接口 (`backend/app/api/llm_provider.py`)

**创建时加密**：
```python
# 第86行
encrypted_api_key = encrypt_api_key(provider.api_key)
```

**查询时脱敏**：
```python
# 第51行、第74行
if provider.api_key:
    provider.api_key = mask_api_key(provider.api_key)
```

**更新时智能处理**：
```python
# 第165-171行
if 'api_key' in update_data and update_data['api_key']:
    # 包含****说明是脱敏格式，前端未修改，跳过更新
    if '****' not in update_data['api_key']:
        update_data['api_key'] = encrypt_api_key(update_data['api_key'])
    else:
        # 保持原值不变
        update_data.pop('api_key')
```

### Workflow-CTL (工作流服务)

#### 1. 加密工具 (`workflow-ctl/app/utils/crypto.py`)

提供与Backend相同的加解密功能，确保两个服务使用相同的密钥和算法。

#### 2. 使用时解密 (`workflow-ctl/app/api/chat.py`)

```python
# 第355行、第464行、第517行
api_key_value = decrypt_api_key(provider.api_key)
```

### Frontend (前端界面)

#### 1. 密钥输入框 (`frontend/src/pages/model/ProviderModal.tsx`)

**显示逻辑**：
```tsx
// 第367-385行
<Input.Password 
  placeholder={mode === 'edit' && originalMaskedApiKey.includes('****')
    ? '保持原密钥不变或输入新密钥'
    : '输入API密钥'
  }
  value={form.api_key || ''}
  onChange={(e) => {
    const newValue = e.target.value;
    setForm(prev => ({ ...prev, api_key: newValue }));
    
    // 检测用户是否修改了密钥
    if (mode === 'edit' && originalMaskedApiKey) {
      setApiKeyModified(newValue !== originalMaskedApiKey && newValue !== '');
    }
  }}
  visibilityToggle={false}
/>
```

**提交逻辑**：
```tsx
// 第273-279行
// 如果是编辑模式且密钥未修改（脱敏格式），保持原值
if (mode === 'edit' && originalMaskedApiKey.includes('****') && !apiKeyModified) {
  submitData.api_key = originalMaskedApiKey;
}
// 否则提交新密钥，后端会进行加密
```

## 配置说明

### 环境变量

在 `.env` 文件中配置加密密钥：

```bash
# API密钥加密密钥 (生产环境必须修改!)
ENCRYPTION_KEY=xinhua-tool-default-encryption-key-change-in-production
```

**⚠️ 重要提醒**：
1. **生产环境必须修改**：默认密钥仅用于开发测试
2. **保持一致**：Backend 和 Workflow-CTL 必须使用相同的 ENCRYPTION_KEY
3. **安全存储**：不要将加密密钥提交到代码仓库
4. **定期更换**：建议定期更换加密密钥（需要重新加密所有现有密钥）

### 生成安全密钥

使用 OpenSSL 生成随机密钥：

```bash
openssl rand -hex 32
```

## 数据流程

### 创建Provider流程

```
用户输入明文密钥
    ↓
前端提交到 Backend
    ↓
Backend: encrypt_api_key()
    ↓
存储加密密钥到数据库
    ↓
同步到 Workflow-CTL 数据库（加密格式）
```

### 查询Provider流程

```
从数据库读取加密密钥
    ↓
Backend: mask_api_key()
    ↓
返回脱敏格式给前端
    ↓
前端显示: sk-****99iJ--goa2xynmofjg
```

### 更新Provider流程

**情况1：不修改密钥**
```
前端保持脱敏格式提交
    ↓
Backend检测到包含****
    ↓
跳过密钥字段更新
    ↓
数据库中密钥保持不变
```

**情况2：修改密钥**
```
用户输入新的明文密钥
    ↓
前端提交新密钥
    ↓
Backend: encrypt_api_key()
    ↓
更新数据库中的加密密钥
```

### 使用Provider流程

```
从数据库读取加密密钥
    ↓
Workflow-CTL: decrypt_api_key()
    ↓
获取明文密钥
    ↓
调用 LLM API
```

## 安全考虑

### 1. 传输安全
- 建议使用 HTTPS 加密传输
- API 密钥在传输过程中应避免明文暴露

### 2. 存储安全
- 数据库中只存储加密后的密钥
- 加密密钥（ENCRYPTION_KEY）应安全存储，不提交到代码仓库

### 3. 使用安全
- 仅在必要时解密（调用API时）
- 解密后的密钥不应写入日志
- 内存中的明文密钥使用后应及时清理

### 4. 访问控制
- API接口需要认证（使用 API Key 认证）
- 限制能够查看和修改密钥的用户权限

## 测试验证

### 1. 创建测试

```bash
# 1. 创建一个新的Provider，输入API密钥
# 2. 检查数据库，确认存储的是加密后的密钥（长字符串）
# 3. 在前端查看，确认显示的是脱敏格式
```

### 2. 更新测试

```bash
# 场景1：不修改密钥
# 1. 编辑Provider但不修改API密钥字段
# 2. 保存后检查数据库，密钥应保持不变

# 场景2：修改密钥
# 1. 编辑Provider并输入新的API密钥
# 2. 保存后检查数据库，密钥应更新为新的加密值
```

### 3. 使用测试

```bash
# 1. 使用聊天接口测试
# 2. 查看workflow-ctl日志，确认成功调用了LLM API
# 3. 确认没有报告密钥解密错误
```

## 故障排查

### 问题1：解密失败

**症状**：日志显示"解密 API 密钥失败"

**可能原因**：
1. ENCRYPTION_KEY 配置不一致
2. 数据库中的密钥是明文（未加密）
3. 加密算法或参数不匹配

**解决方案**：
1. 检查 `.env` 文件中的 ENCRYPTION_KEY 是否一致
2. 重新加密存储所有API密钥
3. 确保Backend和Workflow-CTL使用相同的加密参数

### 问题2：密钥更新失败

**症状**：修改密钥后仍使用旧密钥

**可能原因**：
1. 前端提交了脱敏格式的密钥
2. Backend未正确识别新密钥

**解决方案**：
1. 检查前端是否正确标记了 `apiKeyModified`
2. 确保新密钥不包含 `****`
3. 查看Backend日志确认是否调用了加密函数

### 问题3：无法调用LLM API

**症状**：chat接口报错，无法连接到LLM服务

**可能原因**：
1. 密钥解密失败
2. 解密后的密钥不正确

**解决方案**：
1. 检查workflow-ctl日志中的解密信息
2. 验证数据库中的加密密钥是否正确
3. 手动测试解密后的密钥是否有效

## 维护建议

### 1. 定期密钥轮换

建议每季度或半年轮换一次加密密钥：

1. 生成新的 ENCRYPTION_KEY
2. 使用旧密钥解密所有现有API密钥
3. 使用新密钥重新加密所有API密钥
4. 更新环境变量中的 ENCRYPTION_KEY
5. 重启所有服务

### 2. 审计日志

建议记录以下操作：
- API密钥的创建时间和创建者
- API密钥的修改时间和修改者
- API密钥的使用频率和最后使用时间

### 3. 备份策略

- 加密密钥（ENCRYPTION_KEY）应有安全的备份
- 数据库备份应包含加密后的API密钥
- 恢复时需要使用相同的加密密钥

## 最佳实践

1. **永远不要记录明文密钥**：在日志中只记录脱敏后的密钥
2. **最小权限原则**：限制能够访问密钥的用户和服务
3. **定期审查**：定期检查未使用的API密钥并删除
4. **监控异常**：监控密钥使用情况，发现异常及时处理
5. **安全更新**：及时更新加密库，修复安全漏洞

## 相关文件

### Backend
- `backend/app/utils/crypto.py` - 加密工具
- `backend/app/api/llm_provider.py` - API接口
- `backend/app/models/llm_provider.py` - 数据模型

### Workflow-CTL
- `workflow-ctl/app/utils/crypto.py` - 加密工具
- `workflow-ctl/app/api/chat.py` - 聊天接口
- `workflow-ctl/app/models/llm_provider.py` - 数据模型

### Frontend
- `frontend/src/pages/model/ProviderModal.tsx` - Provider编辑界面
- `frontend/src/pages/model/ModelPage.tsx` - Provider列表页面

### 配置
- `env.example` - 环境变量模板
- `env.production` - 生产环境配置

## 总结

本系统实现了完整的API密钥加密存储解决方案，涵盖了：
- ✅ 加密存储：使用 Fernet 对称加密
- ✅ 脱敏显示：前端只显示部分字符
- ✅ 智能更新：自动识别是否需要加密
- ✅ 透明解密：使用时自动解密
- ✅ 安全配置：支持自定义加密密钥

这确保了敏感信息的安全性，同时提供了良好的用户体验。

