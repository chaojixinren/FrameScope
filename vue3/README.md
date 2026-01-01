# 视频内容理解分析系统 - 前端项目

## 项目简介

这是一个基于 Vue 3 + TypeScript 的视频内容理解分析系统的前端应用。核心功能是同时分析多个视频，提取共同描述、矛盾点和独特特征。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP 客户端**: Axios
- **构建工具**: Vite
- **设计风格**: 参考 ChatGPT Web 的极简专业风格

## 项目结构

```
vue3/
├── src/
│   ├── api/                  # API 接口定义
│   │   ├── index.ts         # Axios 实例配置
│   │   ├── auth.ts          # 认证相关 API（登录、注册）
│   │   └── task.ts          # 任务相关 API（创建、查询、分析）
│   ├── components/          # 组件
│   │   ├── Sidebar.vue     # 侧边栏（历史任务列表）
│   │   └── Header.vue      # 顶部导航栏（主题切换、用户信息）
│   ├── layouts/            # 布局组件
│   │   └── MainLayout.vue  # 主布局（侧边栏 + 主内容区）
│   ├── pages/              # 页面组件
│   │   ├── Login.vue       # 登录页
│   │   ├── Register.vue    # 注册页
│   │   ├── Home.vue        # 首页（创建任务）
│   │   └── TaskDetail.vue  # 任务详情页（显示分析结果）
│   ├── router/             # 路由配置
│   │   └── index.ts        # 路由定义和守卫
│   ├── stores/             # Pinia Store
│   │   ├── user.ts         # 用户状态（登录信息、Token）
│   │   ├── theme.ts        # 主题状态（浅色/深色模式）
│   │   └── task.ts         # 任务状态（任务列表、当前任务）
│   ├── styles/             # 样式文件
│   │   └── theme.css       # ChatGPT 风格主题系统
│   ├── App.vue             # 根组件
│   ├── main.ts             # 入口文件
│   └── style.css           # 基础样式
├── public/                 # 静态资源
├── index.html             # HTML 模板
├── vite.config.ts         # Vite 配置
├── tsconfig.json          # TypeScript 配置
└── package.json           # 依赖配置
```

## 核心功能

### 1. 用户认证
- 登录/注册界面
- Token 自动管理（存储、刷新、过期处理）
- 路由守卫保护

### 2. 任务管理
- 创建分析任务（支持多个视频链接）
- 历史任务列表（侧边栏展示）
- 任务详情查看（分析结果展示）

### 3. 分析结果展示
- **共同描述**: 所有视频的共同观点
- **矛盾点**: 不同视频之间的观点冲突
- **独特特征**: 每个视频独有的特色内容

### 4. 主题系统
- 浅色/深色模式切换
- 遵循系统偏好
- 平滑过渡动画

## 设计特点

### 视觉风格
- 极简、理性、专业的设计语言
- 中性灰、浅白、深灰为主色调
- 低饱和强调色用于关键操作
- 充足的留白，舒适的阅读体验

### 交互体验
- 对话式任务流
- 即时反馈
- 流畅的过渡动画
- 清晰的信息层级

## 开发指南

### 安装依赖
```bash
npm install
```

### 启动开发服务器
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

### 预览生产构建
```bash
npm run preview
```

## API 联调

目前所有 API 调用都使用模拟数据。联调后端时，请参考 `API_INTEGRATION.md` 文档。

主要需要替换的文件：
- `src/api/auth.ts` - 认证相关 API
- `src/api/task.ts` - 任务相关 API

### 配置后端地址

创建 `.env.local` 文件：
```
VITE_API_BASE_URL=http://your-backend-url/api
```

## 路由说明

- `/login` - 登录页
- `/register` - 注册页
- `/` - 首页（创建任务）
- `/task/:id` - 任务详情页

所有需要认证的路由都有路由守卫保护。

## 状态管理

### User Store
- `user`: 当前用户信息
- `token`: 认证 Token
- `isAuthenticated`: 是否已认证

### Theme Store
- `theme`: 当前主题（light/dark）
- `toggleTheme()`: 切换主题
- `initTheme()`: 初始化主题

### Task Store
- `tasks`: 任务列表
- `currentTask`: 当前选中的任务
- `addTask()`: 添加任务
- `updateTask()`: 更新任务
- `loadTasks()`: 从本地存储加载任务

## 样式系统

使用 CSS 变量实现主题系统，支持：
- 浅色模式
- 深色模式
- 平滑过渡

主要变量：
- `--bg-primary`: 主背景色
- `--bg-secondary`: 次背景色
- `--text-primary`: 主文本色
- `--text-secondary`: 次文本色
- `--accent-blue`: 强调色（按钮、链接）
- `--border-light`: 边框色

## 注意事项

1. **API 模拟**: 当前所有 API 都是模拟的，联调时需要替换
2. **本地存储**: 任务数据存储在 localStorage 中，生产环境建议使用后端存储
3. **Token 管理**: Token 存储在 localStorage，请确保在生产环境中使用安全的方式管理

## 后续优化方向

- [ ] 添加视频链接验证（YouTube、Bilibili 等）
- [ ] 优化移动端适配
- [ ] 添加分析进度实时更新（WebSocket）
- [ ] 支持任务导出（PDF、Markdown）
- [ ] 添加任务搜索和筛选功能
- [ ] 优化长文本显示（折叠、展开）
