# AI User Research

AI驱动的用户研究平台 - 演示如何使用三种Agent框架实现四种用户研究场景

## 框架选型

本项目演示如何使用三种Agent框架实现四种用户研究场景：

- **Claude Agent SDK**: 1对1受众访谈（Agentic Loop + MCP）
- **Agno Framework**: 问卷批量投放（Teams）+ 焦点小组批量（Workflows）
- **SmolaAgents**: 受众生成流水线（Manager模式）

## 功能特性

- **AI问卷调研**: 基于人格画像生成真实用户回答
- **焦点小组访谈**: AI模拟真实焦点小组讨论
- **受众管理**: 创建和管理研究受众群体
- **洞察分析**: 自动提取用户研究洞察

## 部署到 Render.com

### 前置要求

- GitHub 账号
- Render.com 账号（免费）
- Anthropic API Key（必需）

### 部署步骤

1. **Fork 或推送此仓库到 GitHub**

2. **在 Render.com 创建新服务**
   - 登录 Render.com
   - 点击 "New +" -> "Web Service"
   - 连接你的 GitHub 仓库
   - Render 会自动检测 `render.yaml` 配置文件

3. **配置环境变量**

   在 Render Dashboard 中设置以下环境变量：

   **必需**:
   - `OPENROUTER_API_KEY`: 你的 OpenRouter API Key（推荐）
   - `OPENROUTER_API_URL`: https://openrouter.ai/api/v1

   **可选**:
   - `ANTHROPIC_API_KEY`: Anthropic API Key（如需直接使用）
   - `OPENAI_API_KEY`: OpenAI API Key（如需使用）
   - `SURVEY_MAX_CONCURRENCY`: 问卷最大并发数（默认100）
   - `FOCUS_GROUP_MAX_CONCURRENCY`: 焦点小组最大并发数（默认50）
   - `LOG_LEVEL`: 日志级别（默认INFO）

4. **部署**
   - 点击 "Create Web Service"
   - Render 会自动构建和部署你的应用

5. **验证部署**

   访问以下端点确认部署成功：
   - `https://your-app.onrender.com/` - 项目信息
   - `https://your-app.onrender.com/health` - 健康检查
   - `https://your-app.onrender.com/docs` - API 文档（Swagger UI）

## 本地开发

### 环境设置

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件：

```env
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_API_URL=https://openrouter.ai/api/v1
ANTHROPIC_API_KEY=your_anthropic_key_here  # 可选
OPENAI_API_KEY=your_openai_key_here  # 可选
SURVEY_MAX_CONCURRENCY=100
FOCUS_GROUP_MAX_CONCURRENCY=50
LOG_LEVEL=INFO
```

### 运行服务

```bash
# 开发模式（支持热重载）
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档

## 快速开始

### 1. 测试核心端点

```bash
# 获取项目信息
curl http://localhost:8000/

# 健康检查
curl http://localhost:8000/health

# 查看配置
curl http://localhost:8000/config
```

### 2. 体验四大场景

访问 Swagger UI 文档：http://localhost:8000/docs

在交互式文档中，你可以：
- 创建受众画像（场景四）
- 创建问卷并投放（场景二）
- 创建焦点小组并运行讨论（场景三）
- 创建1对1访谈会话（场景一）

### 3. 使用 Postman 测试

详细的 Postman 测试步骤请参考 [部署文档 - 测试API章节](DEPLOY.md#测试-api)

## API 端点

### 核心端点

- `GET /` - 项目信息
- `GET /health` - 健康检查
- `GET /config` - 配置信息
- `GET /docs` - Swagger UI 文档
- `GET /redoc` - ReDoc 文档

### 场景一：1对1受众访谈（Claude Agent SDK）

**框架**: Claude Agent SDK + MCP Tools

- `POST /api/interviews` - 创建访谈会话
- `POST /api/interviews/{interview_id}/messages` - 发送访谈消息
- `POST /api/interviews/{interview_id}/end` - 结束访谈
- `GET /api/interviews/{interview_id}` - 获取访谈会话详情
- `GET /api/interviews/{interview_id}/messages` - 获取访谈消息历史

### 场景二：问卷批量投放（Agno Teams）

**框架**: Agno Framework - Teams 模式

- `POST /api/surveys` - 创建问卷
- `POST /api/surveys/{survey_id}/deploy` - 批量投放问卷（异步任务）
- `GET /api/surveys/{survey_id}/tasks/{task_id}` - 查询投放进度
- `GET /api/surveys/{survey_id}/results` - 获取问卷结果
- `GET /api/surveys/{survey_id}` - 获取问卷详情
- `GET /api/surveys` - 获取问卷列表

### 场景三：焦点小组批量（Agno Workflows）

**框架**: Agno Framework - Workflows 模式

- `POST /api/focus-group` - 创建焦点小组
- `POST /api/focus-group/{focus_group_id}/participants` - 添加参与者
- `POST /api/focus-group/{focus_group_id}/batch-participant-response` - 批量生成参与者回答（异步任务）
- `GET /api/focus-group/{focus_group_id}/batch-task/{task_id}` - 查询批量任务进度
- `GET /api/focus-group/{focus_group_id}/active-batch-task` - 获取活跃批量任务
- `GET /api/focus-group/{focus_group_id}/insights` - 获取洞察分析
- `GET /api/focus-group/{focus_group_id}` - 获取焦点小组详情
- `GET /api/focus-group/{focus_group_id}/messages` - 获取讨论消息

### 场景四：受众生成流水线（SmolaAgents Manager）

**框架**: SmolaAgents - Manager Pattern

- `POST /api/audiences/generate` - 生成单个受众画像
- `POST /api/audiences/batch-generate` - 批量生成受众（异步任务）
- `GET /api/audiences/tasks/{task_id}` - 查询批量生成进度
- `GET /api/audiences/{audience_id}` - 获取受众详情
- `GET /api/audiences` - 获取受众列表

## 技术栈

- **Web 框架**: FastAPI
- **ASGI 服务器**: Uvicorn
- **AI 模型**: Anthropic Claude, OpenAI GPT
- **部署平台**: Render.com

## 文档

详细文档请参考 `docs/` 目录：

- [项目需求文档](docs/01-项目需求文档.md)
- [技术架构文档](docs/02-技术架构文档.md)
- [设计文档](docs/03-设计文档.md)
- [API示例文档](docs/04-API示例文档.md)

## 许可证

MIT License

## 支持

如有问题，请提交 Issue 或联系维护者。
