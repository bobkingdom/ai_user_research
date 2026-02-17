# Render.com 部署指南

## 文件清单

### 核心部署文件

1. **render.yaml** - Render.com 部署配置
   - 位置: `/Users/anoxia/workspaces/Tests/siry_ai_research/render.yaml`
   - 服务类型: Web Service
   - 运行时: Python 3.11
   - 计划: Free (免费层)

2. **src/main.py** - FastAPI 应用入口
   - 位置: `/Users/anoxia/workspaces/Tests/siry_ai_research/src/main.py`
   - 框架: FastAPI
   - 服务器: Uvicorn

3. **requirements.txt** - Python 依赖
   - 位置: `/Users/anoxia/workspaces/Tests/siry_ai_research/requirements.txt`
   - 核心依赖: FastAPI, Uvicorn, Pydantic

## 部署配置详情

### 服务配置 (render.yaml)

```yaml
服务名称: siry-ai-research
运行时: python
区域: oregon
计划: free
分支: main
```

### 构建命令

```bash
pip install -r requirements.txt
```

### 启动命令

```bash
uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

### 环境变量

#### 必需变量
- `ANTHROPIC_API_KEY` - Anthropic Claude API密钥（需手动配置）

#### 可选变量
- `OPENAI_API_KEY` - OpenAI API密钥
- `OPENROUTER_API_KEY` - OpenRouter API密钥
- `SURVEY_MAX_CONCURRENCY` - 问卷最大并发数（默认: 100）
- `FOCUS_GROUP_MAX_CONCURRENCY` - 焦点小组最大并发数（默认: 50）
- `LOG_LEVEL` - 日志级别（默认: INFO）
- `PYTHON_VERSION` - Python版本（默认: 3.11.0）

### 健康检查

- **路径**: `/health`
- **检查项**:
  - Anthropic API配置状态
  - OpenAI API配置状态
  - OpenRouter API配置状态
  - 服务运行状态

## API 端点

### 核心端点

| 方法 | 路径 | 描述 |
|-----|------|------|
| GET | `/` | 项目信息和功能列表 |
| GET | `/health` | 健康检查（Render监控用） |
| GET | `/config` | 配置信息（不含敏感数据） |
| GET | `/docs` | Swagger UI 文档 |
| GET | `/redoc` | ReDoc 文档 |

## 部署步骤

### 1. 准备代码仓库

```bash
cd /Users/anoxia/workspaces/Tests/siry_ai_research
git init
git add .
git commit -m "Initial commit: Render.com deployment setup"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. 在 Render.com 创建服务

1. 登录 [Render.com](https://render.com)
2. 点击 "New +" → "Web Service"
3. 连接你的 GitHub 仓库
4. Render 会自动检测 `render.yaml` 配置

### 3. 配置环境变量

在 Render Dashboard 中添加：

```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

可选配置（根据需要）：
```
OPENAI_API_KEY=your_openai_key
OPENROUTER_API_KEY=your_openrouter_key
```

### 4. 部署

- 点击 "Create Web Service"
- Render 会自动构建和部署
- 等待构建完成（通常2-3分钟）

### 5. 验证部署

访问你的服务 URL：

```
https://your-app-name.onrender.com/
https://your-app-name.onrender.com/health
https://your-app-name.onrender.com/docs
```

## 本地开发

### 快速启动

```bash
# 使用启动脚本
./start.sh
```

### 手动启动

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys

# 启动服务
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 访问本地服务

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- 项目信息: http://localhost:8000/

## 注意事项

### Free Plan 限制

Render.com 免费计划限制：
- 服务在15分钟无活动后会休眠
- 首次唤醒可能需要30-60秒
- 每月750小时免费运行时间
- 100GB带宽/月

### 性能优化建议

1. **使用健康检查监控**: Render 会定期调用 `/health` 端点
2. **配置自动部署**: 推送到主分支自动部署（已配置）
3. **监控日志**: 在 Render Dashboard 查看实时日志

### 安全建议

1. **不要提交 .env 文件**: 已在 `.gitignore` 中排除
2. **使用环境变量**: 敏感信息只在 Render Dashboard 配置
3. **API Key 安全**: 定期轮换 API Keys
4. **CORS 配置**: 生产环境应限制允许的域名

## 故障排查

### 构建失败

- 检查 `requirements.txt` 依赖版本
- 查看 Render 构建日志
- 确认 Python 版本兼容性

### 服务无法启动

- 检查环境变量是否正确配置
- 查看 Render 日志中的错误信息
- 验证 `ANTHROPIC_API_KEY` 是否有效

### 健康检查失败

- 访问 `/health` 端点查看详细状态
- 检查 API Keys 配置
- 查看服务日志

## 下一步

部署成功后，你可以：

1. 添加更多 API 端点（问卷、焦点小组等）
2. 集成数据库（PostgreSQL）
3. 添加认证和授权
4. 配置自定义域名
5. 升级到付费计划获得更好性能

## 相关文档

- [Render Python 部署文档](https://render.com/docs/deploy-fastapi)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [项目技术架构文档](docs/02-技术架构文档.md)
- [API 示例文档](docs/04-API示例文档.md)

## 支持

遇到问题？
- 查看 Render 部署日志
- 检查健康检查端点
- 联系项目维护者
