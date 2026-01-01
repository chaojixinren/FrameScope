# Google Custom Search API 设置指南

## 问题说明

Google Custom Search JSON API 需要两个参数：
1. **API Key**（已配置：`AIzaSyAAFi02nzkteEEKCSsL4s3UG1niJHsi1yQ`）
2. **Custom Search Engine ID (CX)**（需要配置）

## 设置步骤

### 步骤 1：创建 Custom Search Engine

1. 访问 [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. 点击 **"Add"** 或 **"创建"** 按钮
3. 填写搜索引擎信息：
   - **搜索引擎名称**：例如 "FrameScope Video Search"
   - **要搜索的网站**：
     - 选择 **"搜索整个网络"**（推荐）
     - 或者选择 **"仅搜索我指定的网站"**，然后添加：
       - `bilibili.com`
       - `douyin.com`
       - `kuaishou.com`
       - `youtube.com`
4. 点击 **"创建"**

### 步骤 2：获取 Search Engine ID (CX)

1. 创建完成后，进入搜索引擎控制面板
2. 点击 **"控制面板"** 或 **"Setup"**
3. 在 **"搜索引擎 ID"** 或 **"Search engine ID"** 部分，复制 ID（格式类似：`017576662512468239146:omuauf_lfve`）

### 步骤 3：配置环境变量

#### 方式 1：使用 .env 文件（推荐）

在 `python/` 目录下创建或编辑 `.env` 文件：

```bash
# Google Custom Search API 配置
GOOGLE_API_KEY=AIzaSyAAFi02nzkteEEKCSsL4s3UG1niJHsi1yQ
GOOGLE_CX=你的Search_Engine_ID
```

#### 方式 2：使用环境变量（Windows PowerShell）

```powershell
$env:GOOGLE_CX="你的Search_Engine_ID"
```

#### 方式 3：使用环境变量（Windows CMD）

```cmd
set GOOGLE_CX=你的Search_Engine_ID
```

#### 方式 4：使用环境变量（Linux/Mac）

```bash
export GOOGLE_CX="你的Search_Engine_ID"
```

### 步骤 4：验证配置

运行测试脚本验证配置：

```bash
cd python
python agent/tests/测试视频url搜索节点.py
```

如果配置正确，应该能看到搜索结果。

## 注意事项

1. **免费配额**：Google Custom Search API 免费版每天提供 100 次搜索请求
2. **API Key 限制**：确保 API Key 已启用 Custom Search API
3. **搜索引擎设置**：如果选择"搜索整个网络"，可能需要等待几分钟才能生效

## 故障排除

### 问题 1：仍然返回 400 错误

- 检查 CX 是否正确配置
- 检查 API Key 是否有效
- 检查是否已启用 Custom Search JSON API

### 问题 2：搜索结果为空

- 检查搜索引擎是否已激活（可能需要等待几分钟）
- 检查搜索引擎设置是否正确（是否选择了"搜索整个网络"）

### 问题 3：配额已用完

- 检查 Google Cloud Console 中的 API 使用情况
- 考虑升级到付费计划

## 快速配置脚本

运行以下 Python 脚本可以快速设置：

```bash
cd python
python setup_google_search.py
```

脚本会引导你输入 CX 并自动配置到 `.env` 文件中。


