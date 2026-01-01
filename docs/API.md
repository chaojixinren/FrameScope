# FrameScope API 文档

## 目录

- [概述](#概述)
- [认证说明](#认证说明)
- [基础信息](#基础信息)
- [API 接口](#api-接口)
  - [认证相关](#1-认证相关)
  - [对话管理](#2-对话管理)
  - [模型提供商管理](#3-模型提供商管理)
  - [模型管理](#4-模型管理)
  - [AI 服务](#5-ai-服务)
  - [系统服务](#6-系统服务)
- [响应格式](#响应格式)
- [错误码说明](#错误码说明)

---

## 概述

FrameScope 是一个基于 LangGraph 的多视频搜索和总结系统，提供完整的用户认证、对话管理和 AI 视频分析功能。

**Base URL**: `http://localhost:8483`

**API 版本**: `v1.0.0`

---

## 认证说明

### JWT Token 认证

大部分接口需要 JWT Token 认证。获取 Token 的方式：

1. **用户注册**：注册成功后自动返回 Token
2. **用户登录**：通过 `/api/auth/login` 或 `/api/auth/login_json` 获取 Token

### 使用 Token

在请求头中添加：

```
Authorization: Bearer <your_token>
```

### Token 有效期

默认有效期为 **24 小时**，可通过环境变量 `JWT_EXPIRATION_HOURS` 配置。

---

## 基础信息

### 请求格式

- **Content-Type**: `application/json`（JSON 接口）或 `application/x-www-form-urlencoded`（表单接口）
- **字符编码**: `UTF-8`

### 响应格式

所有接口统一返回以下格式：

```json
{
  "code": 0,
  "msg": "操作成功",
  "data": {}
}
```

- `code`: 状态码（0 表示成功，其他值表示失败）
- `msg`: 提示信息
- `data`: 返回数据（成功时包含，失败时可能为空）

---

## API 接口

### 1. 认证相关

#### 1.1 用户注册

**接口**: `POST /api/auth/register`

**说明**: 注册新用户账户

**是否需要认证**: 否

**请求参数**:

```json
{
  "username": "string",        // 必填，用户名（唯一）
  "password": "string",        // 必填，密码（至少6位）
  "phone_number": "string",    // 可选，手机号（唯一）
  "avatar": "string"          // 可选，头像URL
}
```

**请求示例**:

```bash
curl -X POST "http://localhost:8483/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "phone_number": "13800138000"
  }'
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "注册成功",
  "data": {
    "user_id": 1,
    "username": "testuser",
    "phone_number": "13800138000",
    "avatar": null,
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

**错误响应**:

```json
{
  "code": 2002,
  "msg": "用户名已存在",
  "data": null
}
```

---

#### 1.2 用户登录（表单格式）

**接口**: `POST /api/auth/login`

**说明**: 使用 OAuth2 标准表单格式登录（支持用户名或手机号）

**是否需要认证**: 否

**请求格式**: `application/x-www-form-urlencoded`

**请求参数**:

- `username`: 用户名或手机号
- `password`: 密码

**请求示例**:

```bash
curl -X POST "http://localhost:8483/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": 1,
    "username": "testuser"
  }
}
```

---

#### 1.3 用户登录（JSON 格式）

**接口**: `POST /api/auth/login_json`

**说明**: 使用 JSON 格式登录（支持用户名或手机号）

**是否需要认证**: 否

**请求参数**:

```json
{
  "username": "string",        // 可选，用户名
  "phone_number": "string",    // 可选，手机号（与username二选一）
  "password": "string"        // 必填，密码
}
```

**请求示例**:

```bash
curl -X POST "http://localhost:8483/api/auth/login_json" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

**响应示例**: 同 1.2

---

#### 1.4 获取当前用户信息

**接口**: `GET /api/auth/me`

**说明**: 获取当前登录用户的详细信息

**是否需要认证**: 是

**请求示例**:

```bash
curl -X GET "http://localhost:8483/api/auth/me" \
  -H "Authorization: Bearer <your_token>"
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "获取用户信息成功",
  "data": {
    "id": 1,
    "username": "testuser",
    "phone_number": "13800138000",
    "avatar": null,
    "is_online": 1,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

---

### 2. 对话管理

#### 2.1 获取对话列表

**接口**: `GET /api/conversations`

**说明**: 获取当前用户的所有对话列表

**是否需要认证**: 是

**查询参数**:

- `limit`: 返回数量限制（默认 50）
- `offset`: 偏移量（默认 0）

**请求示例**:

```bash
curl -X GET "http://localhost:8483/api/conversations?limit=10&offset=0" \
  -H "Authorization: Bearer <your_token>"
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "获取对话列表成功",
  "data": {
    "conversations": [
      {
        "id": 1,
        "user_id": 1,
        "title": "关于索尼A7M4的讨论",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
      }
    ],
    "total": 1,
    "limit": 10,
    "offset": 0
  }
}
```

---

#### 2.2 创建对话

**接口**: `POST /api/conversations`

**说明**: 创建新对话

**是否需要认证**: 是

**请求参数**:

```json
{
  "title": "string"  // 可选，对话标题（默认为空，后续可自动生成）
}
```

**请求示例**:

```bash
curl -X POST "http://localhost:8483/api/conversations" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "新对话"
  }'
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "创建对话成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "title": "新对话",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

---

#### 2.3 获取对话详情

**接口**: `GET /api/conversations/{conversation_id}`

**说明**: 获取指定对话的详情和所有消息

**是否需要认证**: 是

**路径参数**:

- `conversation_id`: 对话ID

**请求示例**:

```bash
curl -X GET "http://localhost:8483/api/conversations/1" \
  -H "Authorization: Bearer <your_token>"
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "获取对话详情成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "title": "关于索尼A7M4的讨论",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
    "messages": [
      {
        "id": 1,
        "role": "user",
        "content": "索尼A7M4相机怎么样？",
        "created_at": "2024-01-01T00:00:00"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "根据多个视频的分析，索尼A7M4...",
        "created_at": "2024-01-01T00:01:00"
      }
    ]
  }
}
```

---

#### 2.4 更新对话标题

**接口**: `PUT /api/conversations/{conversation_id}/title`

**说明**: 更新指定对话的标题

**是否需要认证**: 是

**路径参数**:

- `conversation_id`: 对话ID

**请求参数**:

```json
{
  "title": "string"  // 必填，新标题
}
```

**请求示例**:

```bash
curl -X PUT "http://localhost:8483/api/conversations/1/title" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的标题"
  }'
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "更新对话标题成功",
  "data": null
}
```

---

#### 2.5 删除对话

**接口**: `DELETE /api/conversations/{conversation_id}`

**说明**: 删除指定对话（会级联删除所有相关消息）

**是否需要认证**: 是

**路径参数**:

- `conversation_id`: 对话ID

**请求示例**:

```bash
curl -X DELETE "http://localhost:8483/api/conversations/1" \
  -H "Authorization: Bearer <your_token>"
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "删除对话成功",
  "data": null
}
```

---

### 3. 模型提供商管理

#### 3.1 添加提供商

**接口**: `POST /api/add_provider`

**说明**: 添加新的模型提供商（如 OpenAI、DeepSeek、Qwen 等）

**是否需要认证**: 否

**请求参数**:

```json
{
  "name": "string",      // 必填，提供商名称
  "api_key": "string",   // 必填，API密钥
  "base_url": "string",  // 必填，API基础URL
  "logo": "string",      // 可选，Logo URL
  "type": "string"      // 必填，提供商类型（如 "openai", "deepseek", "qwen"）
}
```

**请求示例**:

```bash
curl -X POST "http://localhost:8483/api/add_provider" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DeepSeek",
    "api_key": "sk-xxx",
    "base_url": "https://api.deepseek.com",
    "type": "deepseek"
  }'
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "添加模型供应商成功",
  "data": {
    "id": "provider_123",
    "name": "DeepSeek",
    "type": "deepseek"
  }
}
```

---

#### 3.2 获取所有提供商

**接口**: `GET /api/get_all_providers`

**说明**: 获取所有已配置的模型提供商列表

**是否需要认证**: 否

**请求示例**:

```bash
curl -X GET "http://localhost:8483/api/get_all_providers"
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "操作成功",
  "data": [
    {
      "id": "provider_123",
      "name": "DeepSeek",
      "type": "deepseek",
      "base_url": "https://api.deepseek.com",
      "enabled": 1
    }
  ]
}
```

---

#### 3.3 根据ID获取提供商

**接口**: `GET /api/get_provider_by_id/{id}`

**说明**: 根据提供商ID获取详细信息

**是否需要认证**: 否

**路径参数**:

- `id`: 提供商ID

**请求示例**:

```bash
curl -X GET "http://localhost:8483/api/get_provider_by_id/provider_123"
```

**响应示例**: 同 3.2（单个对象）

---

#### 3.4 更新提供商

**接口**: `POST /api/update_provider`

**说明**: 更新提供商信息（部分字段可选）

**是否需要认证**: 否

**请求参数**:

```json
{
  "id": "string",           // 必填，提供商ID
  "name": "string",         // 可选，名称
  "api_key": "string",      // 可选，API密钥
  "base_url": "string",     // 可选，基础URL
  "logo": "string",         // 可选，Logo URL
  "type": "string",         // 可选，类型
  "enabled": 1              // 可选，是否启用（0/1）
}
```

**请求示例**:

```bash
curl -X POST "http://localhost:8483/api/update_provider" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "provider_123",
    "api_key": "sk-new-key",
    "enabled": 1
  }'
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "更新模型供应商成功",
  "data": {
    "id": "provider_123"
  }
}
```

---

### 4. 模型管理

#### 4.1 获取所有模型列表

**接口**: `GET /api/model_list`

**说明**: 获取所有已配置的模型列表

**是否需要认证**: 否

**请求示例**:

```bash
curl -X GET "http://localhost:8483/api/model_list"
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "获取模型列表成功",
  "data": [
    {
      "id": 1,
      "provider_id": "provider_123",
      "model_name": "deepseek-chat",
      "enabled": 1
    }
  ]
}
```

---

#### 4.2 根据提供商ID获取模型列表

**接口**: `GET /api/model_list/{provider_id}`

**说明**: 获取指定提供商下的所有模型

**是否需要认证**: 否

**路径参数**:

- `provider_id`: 提供商ID

**请求示例**:

```bash
curl -X GET "http://localhost:8483/api/model_list/provider_123"
```

**响应示例**: 同 4.1

---

#### 4.3 添加模型

**接口**: `POST /api/models`

**说明**: 为指定提供商添加新模型

**是否需要认证**: 否

**请求参数**:

```json
{
  "provider_id": "string",  // 必填，提供商ID
  "model_name": "string"    // 必填，模型名称
}
```

**请求示例**:

```bash
curl -X POST "http://localhost:8483/api/models" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "provider_123",
    "model_name": "deepseek-chat"
  }'
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "模型添加成功",
  "data": null
}
```

---

#### 4.4 删除模型

**接口**: `GET /api/models/delete/{model_id}`

**说明**: 删除指定模型

**是否需要认证**: 否

**路径参数**:

- `model_id`: 模型ID

**请求示例**:

```bash
curl -X GET "http://localhost:8483/api/models/delete/1"
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "模型删除成功",
  "data": null
}
```

---

#### 4.5 获取启用模型

**接口**: `GET /api/model_enable/{provider_id}`

**说明**: 获取指定提供商下所有已启用的模型

**是否需要认证**: 否

**路径参数**:

- `provider_id`: 提供商ID

**请求示例**:

```bash
curl -X GET "http://localhost:8483/api/model_enable/provider_123"
```

**响应示例**: 同 4.1

---

### 5. AI 服务

#### 5.1 多视频搜索和总结

**接口**: `POST /api/multi_video`

**说明**: 核心AI服务接口，执行多视频搜索、笔记生成和总结的完整工作流

**是否需要认证**: 是

**工作流程**:
1. 根据用户问题搜索 Bilibili 相关视频
2. 并发生成每个视频的笔记（包含转录文本）
3. 对多个笔记进行多角度总结
4. 生成关键帧证据链（可选）
5. 自动保存对话和消息

**请求参数**:

```json
{
  "question": "string",              // 必填，用户问题（1-5000字符）
  "session_id": "string",           // 可选，会话ID
  "conversation_id": 1,              // 可选，对话ID（如果提供则加载历史消息）
  "model_name": "string",            // 可选，模型名称（不提供则使用默认）
  "provider_id": "string"            // 可选，提供商ID（不提供则使用默认）
}
```

**请求示例**:

```bash
curl -X POST "http://localhost:8483/api/multi_video" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "索尼A7M4相机怎么样？",
    "conversation_id": 1
  }'
```

**响应示例**:

```json
{
  "success": true,
  "answer": "# 索尼A7M4相机评测总结\n\n根据多个视频的分析...\n\n![关键帧 @ 03:45](/static/screenshots/frame_xxx.jpg)\n\n[查看原片 @ 03:45](https://www.bilibili.com/video/BVxxx?t=225)",
  "metadata": {
    "total_videos": 5,
    "processing_time": 120.5
  }
}
```

**响应字段说明**:

- `success`: 是否成功
- `answer`: 生成的总结内容（Markdown格式，包含关键帧图片链接）
- `metadata`: 元数据信息
  - `total_videos`: 处理的视频数量
  - `processing_time`: 处理耗时（秒）

**注意事项**:

- 此接口会消耗较长时间（通常 1-5 分钟），取决于视频数量和长度
- 如果提供了 `conversation_id`，系统会自动加载历史消息作为上下文
- 处理完成后，用户问题和AI回答会自动保存到对话中
- 如果对话标题为空，系统会自动生成标题

---

### 6. 系统服务

#### 6.1 健康检查

**接口**: `GET /health`

**说明**: 检查服务是否正常运行（用于监控和负载均衡）

**是否需要认证**: 否

**请求示例**:

```bash
curl -X GET "http://localhost:8483/health"
```

**响应示例**:

```json
{
  "status": "healthy",
  "service": "python-ai",
  "version": "1.0.0"
}
```

---

## 响应格式

### 成功响应

```json
{
  "code": 0,
  "msg": "操作成功",
  "data": {
    // 具体数据
  }
}
```

### 错误响应

```json
{
  "code": 3001,
  "msg": "认证失败",
  "data": null
}
```

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 通用失败 |
| 1001 | 下载错误 |
| 1002 | 转录错误 |
| 1003 | 生成错误 |
| 2001 | 无效URL |
| 2002 | 参数错误 |
| 3001 | 认证错误 |
| 3002 | Token过期 |
| 3003 | 权限不足 |
| 4001 | 对话不存在 |
| 4002 | 对话访问被拒绝 |

---

## 使用示例

### 完整工作流示例

```bash
# 1. 注册用户
curl -X POST "http://localhost:8483/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# 2. 登录获取Token
TOKEN=$(curl -X POST "http://localhost:8483/api/auth/login_json" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }' | jq -r '.data.access_token')

# 3. 创建对话
CONV_ID=$(curl -X POST "http://localhost:8483/api/conversations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "测试对话"}' | jq -r '.data.id')

# 4. 执行多视频搜索和总结
curl -X POST "http://localhost:8483/api/multi_video" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"索尼A7M4相机怎么样？\",
    \"conversation_id\": $CONV_ID
  }"

# 5. 获取对话详情（查看历史消息）
curl -X GET "http://localhost:8483/api/conversations/$CONV_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 注意事项

1. **认证要求**: 大部分接口需要 JWT Token 认证，请确保在请求头中包含有效的 Token
2. **Token 有效期**: Token 默认有效期为 24 小时，过期后需要重新登录
3. **请求频率**: 建议控制请求频率，避免对服务器造成过大压力
4. **多视频接口**: `/api/multi_video` 接口处理时间较长，建议设置合适的超时时间
5. **错误处理**: 所有接口都可能返回错误，请根据 `code` 字段进行错误处理
6. **数据格式**: 所有时间字段使用 ISO 8601 格式（如 `2024-01-01T00:00:00`）

---

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持用户认证和对话管理
- 支持多视频搜索和总结功能
- 支持模型提供商和模型管理

---

## 技术支持

如有问题或建议，请联系开发团队。

