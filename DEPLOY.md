# AI User Research 部署指南

## 目录
- [前置要求](#前置要求)
- [后端部署](#后端部署)
- [前端部署](#前端部署)
- [Nginx 配置](#nginx-配置)
- [Systemd 服务配置](#systemd-服务配置)
- [故障排查](#故障排查)

---

## 前置要求

### 服务器环境
- Ubuntu/CentOS/Rocky Linux
- Python 3.10+ (推荐 3.10.19)
- Nginx
- Git
- 至少 2GB RAM

### API Keys
- OpenRouter API Key（推荐）或
- Anthropic API Key 或
- OpenAI API Key

---

## 后端部署

### 1. 克隆代码

```bash
# 创建部署目录
mkdir -p /anoxia/server
cd /anoxia/server

# 克隆仓库
git clone https://github.com/bobkingdom/ai_user_research.git
cd ai_user_research
```

### 2. 安装 Python 3.10（如果没有）

#### 使用 pyenv（推荐）
```bash
# 安装 pyenv
curl https://pyenv.run | bash

# 添加到 ~/.bashrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# 安装 Python 3.10.19
pyenv install 3.10.19
```

#### 使用系统包管理器
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev

# CentOS/Rocky Linux
sudo yum install python310 python310-devel
```

### 3. 创建虚拟环境

#### 方法 A：使用 pyenv
```bash
cd /anoxia/server/ai_user_research

# 使用 pyenv 的 Python 创建虚拟环境
~/.pyenv/versions/3.10.19/bin/python3 -m venv venv
```

#### 方法 B：使用系统 Python
```bash
cd /anoxia/server/ai_user_research
python3.10 -m venv venv
```

### 4. 安装依赖

```bash
# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 验证安装
python --version  # 应该显示 Python 3.10.x
```

### 5. 配置环境变量

创建 `.env` 文件：

```bash
cat > .env << 'EOF'
# OpenRouter API (推荐)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_API_URL=https://openrouter.ai/api/v1

# 或者使用 Anthropic API
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# 或者使用 OpenAI API
# OPENAI_API_KEY=sk-your-key-here

# 并发配置
SURVEY_MAX_CONCURRENCY=100
FOCUS_GROUP_MAX_CONCURRENCY=50

# 日志级别
LOG_LEVEL=INFO

# 端口（内部端口，nginx 会反向代理）
PORT=8002
EOF
```

**重要**：将 `your-key-here` 替换为你的实际 API Key

### 6. 测试运行

```bash
# 激活虚拟环境
source venv/bin/activate

# 测试运行
uvicorn src.main:app --host 0.0.0.0 --port 8002

# 在另一个终端测试
curl http://localhost:8002/
curl http://localhost:8002/health
```

如果看到 JSON 响应，说明后端运行正常。按 `Ctrl+C` 停止。

---

## 前端部署

### 说明
目前项目是纯后端 API 项目，没有前端代码。前端需要单独开发。

### 如果你有前端项目

#### 1. Vue.js / React / Angular 项目

```bash
# 克隆前端项目
cd /anoxia/server
git clone <your-frontend-repo>
cd <frontend-project>

# 安装依赖
npm install

# 构建生产版本
npm run build

# 构建产物通常在 dist/ 目录
```

#### 2. 配置 API Base URL

在前端项目的环境配置文件中（如 `.env.production`）：

```env
# Vue.js
VUE_APP_API_BASE_URL=https://siry.ai

# React
REACT_APP_API_BASE_URL=https://siry.ai

# Angular (environment.prod.ts)
apiUrl: 'https://siry.ai'
```

---

## Nginx 配置

### 1. 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/Rocky Linux
sudo yum install nginx

# 启动 nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 2. 配置 SSL 证书

将你的 SSL 证书文件放到 `/etc/nginx/` 目录：

```bash
# 上传证书文件
sudo cp siry.ai.pem /etc/nginx/
sudo cp siry.ai.key /etc/nginx/

# 设置权限
sudo chmod 600 /etc/nginx/siry.ai.key
sudo chmod 644 /etc/nginx/siry.ai.pem
```

### 3. 创建 Nginx 配置

#### 仅后端 API 的配置

创建文件 `/etc/nginx/conf.d/ai_user_research.conf`：

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name siry.ai www.siry.ai;
    return 301 https://$host$request_uri;
}

# HTTPS 服务
server {
    listen 443 ssl;
    server_name siry.ai www.siry.ai;

    # SSL 证书配置
    ssl_certificate /etc/nginx/siry.ai.pem;
    ssl_certificate_key /etc/nginx/siry.ai.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 反向代理到 FastAPI
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # 超时设置（焦点小组批量生成可能需要较长时间）
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # API 文档路径（可选：如果不想公开，可以删除）
    location /docs {
        proxy_pass http://127.0.0.1:8002/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8002/redoc;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 带前端的配置（如果有前端项目）

创建文件 `/etc/nginx/conf.d/ai_user_research.conf`：

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name siry.ai www.siry.ai;
    return 301 https://$host$request_uri;
}

# HTTPS 服务
server {
    listen 443 ssl;
    server_name siry.ai www.siry.ai;

    # SSL 证书配置
    ssl_certificate /etc/nginx/siry.ai.pem;
    ssl_certificate_key /etc/nginx/siry.ai.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 前端静态文件（根路径）
    location / {
        root /anoxia/server/frontend/dist;  # 前端构建产物目录
        index index.html;
        try_files $uri $uri/ /index.html;  # SPA 路由支持
    }

    # API 请求转发到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8002/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # 健康检查端点
    location /health {
        proxy_pass http://127.0.0.1:8002/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # API 文档（可选）
    location /docs {
        proxy_pass http://127.0.0.1:8002/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8002/redoc;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

### 4. 测试和重载 Nginx

```bash
# 测试配置文件语法
sudo nginx -t

# 如果测试通过，重载配置
sudo nginx -s reload

# 或者重启 nginx
sudo systemctl restart nginx
```

---

## Systemd 服务配置

### 1. 创建 Systemd 服务文件

创建文件 `/etc/systemd/system/ai_user_research.service`：

```ini
[Unit]
Description=AI User Research API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/anoxia/server/ai_user_research
Environment="PATH=/anoxia/server/ai_user_research/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="OPENROUTER_API_KEY=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"
Environment="OPENROUTER_API_URL=https://openrouter.ai/api/v1"
Environment="SURVEY_MAX_CONCURRENCY=100"
Environment="FOCUS_GROUP_MAX_CONCURRENCY=50"
Environment="LOG_LEVEL=INFO"
Environment="PORT=8002"
ExecStart=/anoxia/server/ai_user_research/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**重要**：将 `OPENROUTER_API_KEY` 的值替换为你的实际 API Key

### 2. 启动服务

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start ai_user_research

# 设置开机自启
sudo systemctl enable ai_user_research

# 查看状态
sudo systemctl status ai_user_research
```

### 3. 查看日志

```bash
# 实时查看日志
sudo journalctl -u ai_user_research -f

# 查看最近 50 行日志
sudo journalctl -u ai_user_research -n 50

# 查看今天的日志
sudo journalctl -u ai_user_research --since today
```

---

## 验证部署

### 1. 检查后端健康状态

```bash
# 本地检查
curl http://localhost:8002/health

# 外部检查
curl https://siry.ai/health
```

预期响应：
```json
{
  "status": "healthy",
  "timestamp": "2026-02-18T03:33:39.095371",
  "checks": {
    "openrouter_api": "configured",
    "anthropic_api": "not_configured",
    "openai_api": "not_configured"
  }
}
```

### 2. 访问 API 文档

在浏览器中访问：
- Swagger UI: https://siry.ai/docs
- ReDoc: https://siry.ai/redoc

### 3. 测试 API 端点

```bash
# 获取项目信息
curl https://siry.ai/

# 获取配置信息
curl https://siry.ai/config
```

---

## 测试 API

### 方法一：使用 Swagger UI（推荐）

1. **访问 Swagger UI**
   ```
   https://siry.ai/docs
   ```

2. **测试核心端点**
   - 点击 `GET /` 展开
   - 点击 "Try it out" 按钮
   - 点击 "Execute" 查看响应

3. **测试场景四：生成受众画像**
   - 展开 `POST /api/audiences/generate`
   - 点击 "Try it out"
   - 修改请求体：
     ```json
     {
       "description": "30岁的互联网产品经理，关注效率工具",
       "generation_config": {
         "model": "claude-3-5-sonnet",
         "max_retries": 3
       }
     }
     ```
   - 点击 "Execute"
   - 查看生成的受众画像

4. **测试场景二：问卷投放**

   a. 创建问卷：
   - 展开 `POST /api/surveys`
   - 点击 "Try it out"
   - 使用示例请求体
   - 记录返回的 `survey_id`

   b. 批量投放（异步）：
   - 展开 `POST /api/surveys/{survey_id}/deploy`
   - 输入上一步得到的 `survey_id`
   - 修改请求体中的 `audience_ids`
   - 点击 "Execute"
   - 记录返回的 `task_id`

   c. 查询进度：
   - 展开 `GET /api/surveys/{survey_id}/tasks/{task_id}`
   - 输入 `survey_id` 和 `task_id`
   - 点击 "Execute"
   - 重复执行直到 `status` 变为 `completed`

   d. 获取结果：
   - 展开 `GET /api/surveys/{survey_id}/results`
   - 输入 `survey_id`
   - 点击 "Execute"
   - 查看问卷结果和统计分析

5. **测试场景三：焦点小组**

   a. 创建焦点小组：
   - 展开 `POST /api/focus-group`
   - 使用示例请求体
   - 记录返回的 `focus_group_id`

   b. 添加参与者：
   - 展开 `POST /api/focus-group/{focus_group_id}/participants`
   - 输入 `focus_group_id`
   - 修改请求体中的 `audience_ids`
   - 点击 "Execute"

   c. 批量生成回答（异步）：
   - 展开 `POST /api/focus-group/{focus_group_id}/batch-participant-response`
   - 输入 `focus_group_id`
   - 修改 `participant_ids` 和 `host_message`
   - 点击 "Execute"
   - 记录返回的 `task_id`

   d. 查询进度：
   - 展开 `GET /api/focus-group/{focus_group_id}/batch-task/{task_id}`
   - 输入 `focus_group_id` 和 `task_id`
   - 点击 "Execute"
   - 重复执行直到完成

   e. 获取洞察：
   - 展开 `GET /api/focus-group/{focus_group_id}/insights`
   - 输入 `focus_group_id`
   - 点击 "Execute"
   - 查看提取的洞察分析

6. **测试场景一：1对1访谈**

   a. 创建访谈会话：
   - 展开 `POST /api/interviews`
   - 修改请求体中的 `audience_id` 和 `topic`
   - 记录返回的 `interview_id`

   b. 发送访谈消息：
   - 展开 `POST /api/interviews/{interview_id}/messages`
   - 输入 `interview_id`
   - 修改 `message` 内容
   - 点击 "Execute"
   - 查看受众的回答

   c. 结束访谈：
   - 展开 `POST /api/interviews/{interview_id}/end`
   - 输入 `interview_id`
   - 点击 "Execute"
   - 查看访谈摘要和洞察

### 方法二：使用 curl 命令

#### 1. 测试健康检查
```bash
curl https://siry.ai/health
```

#### 2. 生成受众画像
```bash
curl -X POST https://siry.ai/api/audiences/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "30岁的互联网产品经理",
    "generation_config": {
      "model": "claude-3-5-sonnet"
    }
  }'
```

#### 3. 创建问卷
```bash
curl -X POST https://siry.ai/api/surveys \
  -H "Content-Type: application/json" \
  -d '{
    "title": "产品满意度调查",
    "questions": [
      {
        "id": "q1",
        "type": "single_choice",
        "content": "您对产品的整体满意度？",
        "options": ["非常满意", "满意", "一般", "不满意"]
      }
    ]
  }'
```

#### 4. 批量投放问卷（异步）
```bash
# 先记录上一步返回的 survey_id
SURVEY_ID="srv-12345"

# 发起投放任务
TASK_RESPONSE=$(curl -X POST https://siry.ai/api/surveys/$SURVEY_ID/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "audience_ids": ["aud-001", "aud-002", "aud-003"],
    "concurrency_config": {
      "max_concurrency": 100
    }
  }')

# 提取 task_id
TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id')
echo "Task ID: $TASK_ID"

# 轮询进度
while true; do
  PROGRESS=$(curl -s https://siry.ai/api/surveys/$SURVEY_ID/tasks/$TASK_ID)
  STATUS=$(echo $PROGRESS | jq -r '.status')
  PERCENTAGE=$(echo $PROGRESS | jq -r '.progress_percentage')

  echo "进度: $PERCENTAGE% (状态: $STATUS)"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi

  sleep 2
done

# 获取结果
curl https://siry.ai/api/surveys/$SURVEY_ID/results
```

#### 5. 创建焦点小组
```bash
curl -X POST https://siry.ai/api/focus-group \
  -H "Content-Type: application/json" \
  -d '{
    "title": "产品需求讨论",
    "topic": "智能家居产品",
    "research_objectives": ["了解用户需求", "探索痛点"]
  }'
```

### 方法三：使用 Postman

#### 1. 导入 Postman Collection（如有）

如果项目提供了 Postman Collection 文件：
```bash
# 查找 Postman Collection
ls -la postman/
```

在 Postman 中：
1. 点击 "Import" 按钮
2. 选择 Collection 文件
3. 导入后在左侧看到所有端点

#### 2. 手动创建请求

a. **设置环境变量**：
   - 点击右上角齿轮图标
   - 创建新环境 "AI User Research"
   - 添加变量：
     - `base_url`: `https://siry.ai`
     - `survey_id`: （运行时更新）
     - `task_id`: （运行时更新）

b. **测试健康检查**：
   - 新建请求
   - 方法：GET
   - URL：`{{base_url}}/health`
   - 点击 "Send"

c. **测试生成受众**：
   - 新建请求
   - 方法：POST
   - URL：`{{base_url}}/api/audiences/generate`
   - Headers：`Content-Type: application/json`
   - Body（raw JSON）：
     ```json
     {
       "description": "30岁的互联网产品经理",
       "generation_config": {
         "model": "claude-3-5-sonnet"
       }
     }
     ```
   - 点击 "Send"

d. **测试异步任务流程**：

   请求1 - 创建问卷：
   - POST `{{base_url}}/api/surveys`
   - 在 Tests 标签添加脚本：
     ```javascript
     pm.environment.set("survey_id", pm.response.json().survey_id);
     ```

   请求2 - 投放问卷：
   - POST `{{base_url}}/api/surveys/{{survey_id}}/deploy`
   - 在 Tests 标签添加脚本：
     ```javascript
     pm.environment.set("task_id", pm.response.json().task_id);
     ```

   请求3 - 查询进度：
   - GET `{{base_url}}/api/surveys/{{survey_id}}/tasks/{{task_id}}`
   - 重复执行直到完成

### 常见测试场景

#### 测试异步任务的防重复机制

1. 发起第一个批量任务：
   ```bash
   curl -X POST https://siry.ai/api/focus-group/fg-123/batch-participant-response \
     -H "Content-Type: application/json" \
     -d '{
       "participant_ids": ["aud-001", "aud-002"],
       "host_message": "大家好，请问..."
     }'
   ```
   返回：`{"task_id": "task-abc", "is_new_task": true}`

2. 在任务完成前，重复发送相同请求：
   ```bash
   # 相同的请求
   curl -X POST https://siry.ai/api/focus-group/fg-123/batch-participant-response \
     -H "Content-Type: application/json" \
     -d '{
       "participant_ids": ["aud-001", "aud-002"],
       "host_message": "大家好，请问..."
     }'
   ```
   返回：`{"task_id": "task-abc", "is_new_task": false}` （返回已存在的任务）

#### 测试进度轮询

使用 shell 脚本自动轮询：
```bash
#!/bin/bash

FOCUS_GROUP_ID="fg-123"
TASK_ID="task-abc"

while true; do
  RESPONSE=$(curl -s https://siry.ai/api/focus-group/$FOCUS_GROUP_ID/batch-task/$TASK_ID)

  STATUS=$(echo $RESPONSE | jq -r '.status')
  PROGRESS=$(echo $RESPONSE | jq -r '.progress_percentage')
  COMPLETED=$(echo $RESPONSE | jq -r '.completed_count')
  TOTAL=$(echo $RESPONSE | jq -r '.total_count')

  echo "[$(date '+%H:%M:%S')] 进度: $COMPLETED/$TOTAL ($PROGRESS%) - 状态: $STATUS"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    echo "任务完成!"
    echo $RESPONSE | jq '.results'
    break
  fi

  sleep 1.5
done
```

---

## 故障排查

### 问题 1: 端口已被占用

**错误信息**: `[Errno 98] Address already in use`

**解决方案**:
```bash
# 查找占用端口的进程
sudo netstat -tlnp | grep 8002
# 或者
sudo ss -tlnp | grep 8002

# 杀死进程
sudo kill <PID>

# 或者更换端口
# 修改 .env 文件中的 PORT
# 修改 systemd 服务文件中的端口
# 修改 nginx 配置中的 proxy_pass 端口
```

### 问题 2: Nginx 403 Forbidden

**解决方案**:
```bash
# 检查文件权限
ls -la /anoxia/server/ai_user_research/

# 确保 nginx 用户有权限访问
sudo chown -R root:root /anoxia/server/ai_user_research/

# 检查 SELinux（CentOS/Rocky）
sudo getenforce
# 如果是 Enforcing，临时关闭测试
sudo setenforce 0
```

### 问题 3: SSL 证书错误

**解决方案**:
```bash
# 检查证书文件是否存在
ls -la /etc/nginx/siry.ai.*

# 检查证书权限
sudo chmod 600 /etc/nginx/siry.ai.key
sudo chmod 644 /etc/nginx/siry.ai.pem

# 测试 SSL 配置
sudo nginx -t
```

### 问题 4: API Key 未加载

**解决方案**:
```bash
# 检查环境变量是否正确加载
sudo systemctl show ai_user_research --property=Environment

# 如果没有显示，检查 service 文件
sudo cat /etc/systemd/system/ai_user_research.service

# 重新加载并重启
sudo systemctl daemon-reload
sudo systemctl restart ai_user_research
```

### 问题 5: Python 版本不对

**错误信息**: `TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument`

**解决方案**:
```bash
# 检查 Python 版本
python --version

# 必须是 Python 3.10+，推荐 3.10.19
# 如果版本不对，重新创建虚拟环境
rm -rf venv
~/.pyenv/versions/3.10.19/bin/python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题 6: 服务无法启动

```bash
# 查看详细错误日志
sudo journalctl -u ai_user_research -n 100 --no-pager

# 检查 WorkingDirectory 是否正确
cd /anoxia/server/ai_user_research
ls -la

# 手动运行测试
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8002
```

---

## 常用维护命令

### 重启服务
```bash
sudo systemctl restart ai_user_research
```

### 查看服务状态
```bash
sudo systemctl status ai_user_research
```

### 更新代码
```bash
cd /anoxia/server/ai_user_research
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart ai_user_research
```

### 备份数据（如果有数据库）
```bash
# 备份数据库
mysqldump -u root -p database_name > backup.sql

# 或者 PostgreSQL
pg_dump -U postgres database_name > backup.sql
```

---

## 安全建议

1. **不要在配置文件中硬编码 API Key**
   - 使用环境变量或密钥管理服务

2. **启用防火墙**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 22/tcp
   sudo ufw enable
   ```

3. **定期更新系统**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **使用非 root 用户运行服务**
   - 修改 systemd 服务文件中的 `User=` 字段

5. **限制 API 访问**
   - 在 nginx 中添加 IP 白名单
   - 使用 API Key 认证

---

## 联系支持

如有问题，请查看：
- 项目文档: `/docs` 目录
- GitHub Issues: https://github.com/bobkingdom/ai_user_research/issues
- API 文档: https://siry.ai/docs

---

**部署完成后，访问 https://siry.ai 验证部署成功！** 🎉
