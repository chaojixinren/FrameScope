# API 联调文档

本文档列出所有需要替换为真实后端 API 调用的位置。

## 配置文件

### 环境变量
在项目根目录创建 `.env` 文件（或 `.env.local`）：
```
VITE_API_BASE_URL=http://your-backend-url/api
```

## 需要替换的 API 调用

### 1. 认证相关 API (`src/api/auth.ts`)

#### 登录接口
**文件**: `src/api/auth.ts`  
**函数**: `authApi.login`  
**当前模拟代码** (第 27-48 行):
```typescript
// 模拟响应
await new Promise(resolve => setTimeout(resolve, 500))
// ... 模拟逻辑
```

**需要替换为**:
```typescript
const response = await api.post<AuthResponse>('/auth/login', data)
return response.data
```

**后端接口要求**:
- **URL**: `POST /auth/login`
- **请求体**: 
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **响应**:
  ```json
  {
    "token": "string",
    "user": {
      "id": "string",
      "username": "string",
      "email": "string"
    }
  }
  ```

---

#### 注册接口
**文件**: `src/api/auth.ts`  
**函数**: `authApi.register`  
**当前模拟代码** (第 51-72 行):
```typescript
// 模拟响应
await new Promise(resolve => setTimeout(resolve, 500))
// ... 模拟逻辑
```

**需要替换为**:
```typescript
const response = await api.post<AuthResponse>('/auth/register', data)
return response.data
```

**后端接口要求**:
- **URL**: `POST /auth/register`
- **请求体**: 
  ```json
  {
    "username": "string",
    "password": "string",
    "email": "string" (可选)
  }
  ```
- **响应**: 同登录接口

---

#### 获取当前用户信息
**文件**: `src/api/auth.ts`  
**函数**: `authApi.getCurrentUser`  
**当前模拟代码** (第 75-87 行):
```typescript
// 模拟响应
await new Promise(resolve => setTimeout(resolve, 300))
// ... 模拟逻辑
```

**需要替换为**:
```typescript
const response = await api.get<AuthResponse['user']>('/auth/me')
return response.data
```

**后端接口要求**:
- **URL**: `GET /auth/me`
- **Headers**: 需要 Bearer Token
- **响应**:
  ```json
  {
    "id": "string",
    "username": "string",
    "email": "string"
  }
  ```

---

### 2. 任务相关 API (`src/api/task.ts`)

#### 创建任务
**文件**: `src/api/task.ts`  
**函数**: `taskApi.createTask`  
**当前模拟代码** (第 12-29 行):
```typescript
// 模拟响应
await new Promise(resolve => setTimeout(resolve, 500))
// ... 模拟逻辑
```

**需要替换为**:
```typescript
const response = await api.post<Task>('/tasks', data)
return response.data
```

**后端接口要求**:
- **URL**: `POST /tasks`
- **Headers**: 需要 Bearer Token
- **请求体**: 
  ```json
  {
    "title": "string"
  }
  ```
- **响应**:
  ```json
  {
    "id": "string",
    "title": "string",
    "videoUrls": ["string"],  // 后端会自动获取并返回视频列表
    "createdAt": "ISO8601 datetime string",
    "updatedAt": "ISO8601 datetime string",
    "status": "pending" | "processing" | "completed" | "error"
  }
  ```

**注意**: 创建任务时不需要提供视频链接，后端会根据任务标题自动获取相关视频。

---

#### 获取任务列表
**文件**: `src/api/task.ts`  
**函数**: `taskApi.getTasks`  
**当前模拟代码** (第 32-40 行):
```typescript
// 模拟响应
await new Promise(resolve => setTimeout(resolve, 300))
return []
```

**需要替换为**:
```typescript
const response = await api.get<Task[]>('/tasks')
return response.data
```

**后端接口要求**:
- **URL**: `GET /tasks`
- **Headers**: 需要 Bearer Token
- **响应**: Task 数组

---

#### 获取任务详情
**文件**: `src/api/task.ts`  
**函数**: `taskApi.getTask`  
**当前模拟代码** (第 43-51 行):
```typescript
// 模拟响应
await new Promise(resolve => setTimeout(resolve, 300))
throw new Error('任务不存在')
```

**需要替换为**:
```typescript
const response = await api.get<Task>(`/tasks/${taskId}`)
return response.data
```

**后端接口要求**:
- **URL**: `GET /tasks/:id`
- **Headers**: 需要 Bearer Token
- **响应**: Task 对象（包含完整结果）

---

#### 开始分析任务
**文件**: `src/api/task.ts`  
**函数**: `taskApi.analyzeTask`  
**当前模拟代码** (第 54-97 行):
```typescript
// 模拟响应 - 延迟模拟分析过程
await new Promise(resolve => setTimeout(resolve, 2000))
// ... 模拟结果数据
```

**需要替换为**:
```typescript
const response = await api.post<Task>(`/tasks/${taskId}/analyze`)
return response.data
```

**后端接口要求**:
- **URL**: `POST /tasks/:id/analyze`
- **Headers**: 需要 Bearer Token
- **响应**: Task 对象（包含分析结果）

**注意**: 如果后端使用异步处理，可能需要通过轮询 `/tasks/:id` 接口来获取分析进度和结果。

---

## Token 处理

### 请求拦截器
`src/api/index.ts` 中的请求拦截器会自动添加 Bearer Token：
```typescript
config.headers.Authorization = `Bearer ${userStore.token}`
```

确保后端接受 `Authorization: Bearer <token>` 格式的请求头。

### 响应拦截器
当收到 401 状态码时，会自动清除登录状态并跳转到登录页。确保后端在 token 无效时返回 401 状态码。

---

## 错误处理

所有 API 调用都应该：
1. 处理网络错误
2. 处理业务错误（后端返回的错误信息）
3. 对于 401 错误，请求拦截器会自动处理
4. 其他错误应该在组件中通过 try-catch 处理

---

## 替换步骤

1. 创建 `.env.local` 文件，设置 `VITE_API_BASE_URL`
2. 逐个替换 `src/api/auth.ts` 和 `src/api/task.ts` 中的模拟代码
3. 确保后端接口符合上述规范
4. 测试所有功能，包括错误处理

---

## 注意事项

- 所有 API 调用都已配置为使用 `api` 实例（来自 `src/api/index.ts`）
- Token 会自动添加到请求头中
- 401 错误会自动处理
- 当前所有模拟 API 都有 `TODO` 注释标记，可以通过搜索 `TODO:` 快速找到需要替换的位置

