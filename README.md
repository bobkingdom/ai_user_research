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

## API 端点

### 核心端点

- `GET /` - 项目信息
- `GET /health` - 健康检查
- `GET /config` - 配置信息
- `GET /docs` - Swagger UI 文档
- `GET /redoc` - ReDoc 文档

### 未来扩展

- `POST /api/surveys` - 创建问卷调研
- `POST /api/focus-groups` - 创建焦点小组
- `POST /api/audiences` - 创建受众群体
- `GET /api/insights` - 获取研究洞察

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
