# API 架构设计文档

## 目录

- [架构概览](#架构概览)
- [四大场景详解](#四大场景详解)
  - [场景一：1对1受众访谈](#场景一1对1受众访谈)
  - [场景二：问卷批量投放](#场景二问卷批量投放)
  - [场景三：焦点小组批量](#场景三焦点小组批量)
  - [场景四：受众生成流水线](#场景四受众生成流水线)
- [技术选型说明](#技术选型说明)
- [异步任务与轮询机制](#异步任务与轮询机制)
- [API调用流程](#api调用流程)

---

## 架构概览

本项目实现了四种用户研究场景，每个场景使用不同的 Agent 框架以展示各框架的最佳实践：

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI User Research                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │  场景一：1对1   │  │ 场景二/三：批量 │  │ 场景四：生成    │     │
│  │  受众访谈       │  │ 问卷/焦点小组   │  │ 受众画像        │     │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘     │
│           │                    │                    │               │
│           ▼                    ▼                    ▼               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ Claude Agent    │  │     Agno        │  │  SmolaAgents    │     │
│  │     SDK         │  │ Teams+Workflows │  │ Manager Pattern │     │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘     │
│           │                    │                    │               │
│           └────────────────────┼────────────────────┘               │
│                                │                                    │
│                                ▼                                    │
│                    ┌─────────────────────┐                         │
│                    │   FastAPI Routers   │                         │
│                    │  (RESTful API 层)   │                         │
│                    └─────────────────────┘                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四大场景详解

### 场景一：1对1受众访谈

#### 使用框架
**Claude Agent SDK + MCP Tools**

#### 技术选型原因
1. **Agentic Loop 架构**：天然适合多轮访谈的"思考-行动-观察"循环
2. **原生 MCP 支持**：可以无缝集成工具生态（personality、chat_history、web_search）
3. **上下文记忆管理**：内置多轮对话上下文，无需手动管理 message history

#### API 端点

##### 1. 创建访谈会话
```
POST /api/interviews
```

**请求体**:
```json
{
  "audience_id": "aud-12345",
  "topic": "效率工具使用体验",
  "research_objectives": [
    "了解日常工作痛点",
    "探索工具选择标准"
  ],
  "mcp_tools": ["personality", "chat_history", "web_search"]
}
```

**响应**:
```json
{
  "interview_id": "itv-abc123",
  "audience_id": "aud-12345",
  "topic": "效率工具使用体验",
  "status": "active",
  "opening_message": "您好，很高兴能和您聊聊...",
  "created_at": "2026-02-18T12:00:00Z"
}
```

##### 2. 发送访谈消息
```
POST /api/interviews/{interview_id}/messages
```

**请求体**:
```json
{
  "message": "您平时工作中最常用的效率工具是什么？"
}
```

**响应**:
```json
{
  "message_id": "msg-xyz789",
  "role": "audience",
  "content": "我主要使用 Notion 来管理项目...",
  "tools_used": ["personality", "chat_history"],
  "created_at": "2026-02-18T12:01:00Z"
}
```

##### 3. 结束访谈
```
POST /api/interviews/{interview_id}/end
```

**响应**:
```json
{
  "interview_id": "itv-abc123",
  "status": "completed",
  "total_rounds": 12,
  "duration_seconds": 1800,
  "summary": "本次访谈深入探讨了...",
  "insights": [
    {
      "content": "用户期望工具具备良好的跨平台同步能力",
      "insight_type": "need",
      "confidence_score": 0.9
    }
  ],
  "emotion_timeline": [
    {"round": 1, "emotion": "neutral"},
    {"round": 5, "emotion": "frustrated"},
    {"round": 12, "emotion": "satisfied"}
  ],
  "ended_at": "2026-02-18T12:30:00Z"
}
```

#### 工作流程图

```
访谈者                Agent SDK                MCP Tools
   │                     │                        │
   │  创建访谈会话       │                        │
   ├────────────────────>│                        │
   │                     │  初始化 Agent         │
   │                     │  加载 MCP Tools       │
   │                     ├──────────────────────>│
   │<────────────────────│                        │
   │  开场白             │                        │
   │                     │                        │
   │  发送问题           │                        │
   ├────────────────────>│                        │
   │                     │  Agentic Loop:        │
   │                     │  1. Gather (收集上下文) │
   │                     ├──────────────────────>│
   │                     │  查询 personality     │
   │                     │<──────────────────────│
   │                     │  2. Action (生成回答)  │
   │                     │  3. Verify (验证一致性)│
   │<────────────────────│                        │
   │  受众回答           │                        │
   │                     │                        │
   │  结束访谈           │                        │
   ├────────────────────>│                        │
   │                     │  提取洞察              │
   │                     │  生成摘要              │
   │<────────────────────│                        │
   │  访谈摘要           │                        │
```

---

### 场景二：问卷批量投放

#### 使用框架
**Agno Framework - Teams 模式**

#### 技术选型原因
1. **天然并行支持**：`Team.run_parallel()` 可以轻松管理100-500并发
2. **Agent 编排能力**：每个受众是一个 Agent，Team 统一管理
3. **内置进度追踪**：框架自动处理任务状态和进度报告

#### API 端点

##### 1. 创建问卷
```
POST /api/surveys
```

**请求体**:
```json
{
  "title": "产品满意度调查",
  "questions": [
    {
      "id": "q1",
      "type": "single_choice",
      "content": "您对当前使用的产品整体满意度如何？",
      "options": ["非常满意", "满意", "一般", "不满意", "非常不满意"]
    },
    {
      "id": "q2",
      "type": "multiple_choice",
      "content": "您最看重产品的哪些特性？（可多选）",
      "options": ["易用性", "功能完整性", "性价比", "客户服务", "品牌信誉"]
    },
    {
      "id": "q3",
      "type": "open_ended",
      "content": "请描述一下您使用产品过程中遇到的最大痛点",
      "max_length": 500
    }
  ]
}
```

**响应**:
```json
{
  "survey_id": "srv-12345",
  "title": "产品满意度调查",
  "questions": [...],
  "status": "draft",
  "created_at": "2026-02-18T12:00:00Z"
}
```

##### 2. 批量投放问卷（异步任务）
```
POST /api/surveys/{survey_id}/deploy
```

**请求体**:
```json
{
  "audience_ids": ["aud-001", "aud-002", "...aud-100"],
  "concurrency_config": {
    "max_concurrency": 100,
    "batch_size": 50
  }
}
```

**响应**（立即返回任务ID）:
```json
{
  "task_id": "task-xyz789",
  "survey_id": "srv-12345",
  "status": "pending",
  "total_count": 100,
  "created_at": "2026-02-18T12:00:00Z"
}
```

##### 3. 查询投放进度
```
GET /api/surveys/{survey_id}/tasks/{task_id}
```

**响应**:
```json
{
  "task_id": "task-xyz789",
  "status": "processing",
  "total_count": 100,
  "completed_count": 75,
  "failed_count": 2,
  "progress_percentage": 75.0,
  "estimated_remaining_seconds": 30,
  "started_at": "2026-02-18T12:00:00Z",
  "updated_at": "2026-02-18T12:01:15Z"
}
```

##### 4. 获取问卷结果
```
GET /api/surveys/{survey_id}/results
```

**响应**:
```json
{
  "survey_id": "srv-12345",
  "total_responses": 98,
  "completion_rate": 98.0,
  "results": {
    "q1": {
      "非常满意": 20,
      "满意": 45,
      "一般": 25,
      "不满意": 6,
      "非常不满意": 2
    },
    "q2": {
      "易用性": 70,
      "功能完整性": 65,
      "性价比": 55,
      "客户服务": 30,
      "品牌信誉": 25
    },
    "q3_clusters": [
      {
        "theme": "性能问题",
        "count": 35,
        "examples": ["加载速度慢", "经常卡顿", "占用内存大"]
      },
      {
        "theme": "功能缺失",
        "count": 28,
        "examples": ["缺少导出功能", "不支持协作", "没有离线模式"]
      }
    ]
  }
}
```

#### 工作流程图

```
客户端                 API Server              Agno Team             受众Agents (100个)
   │                     │                        │                      │
   │  投放问卷(异步)     │                        │                      │
   ├────────────────────>│                        │                      │
   │                     │  创建任务               │                      │
   │                     │  初始化 Team           │                      │
   │                     ├───────────────────────>│                      │
   │                     │                        │  为每个受众创建Agent │
   │                     │                        ├─────────────────────>│
   │<────────────────────│                        │                      │
   │  返回 task_id       │                        │                      │
   │                     │                        │  并行执行问卷        │
   │                     │                        │<────────────────────>│
   │                     │                        │  (100并发，批次50)   │
   │                     │                        │                      │
   │  轮询进度(1-2秒)    │                        │                      │
   ├────────────────────>│                        │                      │
   │                     │  查询任务进度          │                      │
   │<────────────────────│                        │                      │
   │  75/100 (75%)       │                        │                      │
   │                     │                        │                      │
   │  ...轮询直到完成... │                        │                      │
   │                     │                        │                      │
   │  获取结果           │                        │                      │
   ├────────────────────>│                        │                      │
   │                     │  聚合分析              │                      │
   │                     │  统计 + 聚类           │                      │
   │<────────────────────│                        │                      │
   │  问卷结果报告       │                        │                      │
```

---

### 场景三：焦点小组批量

#### 使用框架
**Agno Framework - Workflows 模式**

#### 技术选型原因
1. **流程编排能力**：Workflows 适合"主持人提问 → 参与者并行回答 → 洞察提取"的固定流程
2. **并行控制**：支持50-200个参与者同时回答
3. **步骤可视化**：每个 WorkflowStep 对应一个讨论阶段

#### API 端点

##### 1. 创建焦点小组
```
POST /api/focus-group
```

**请求体**:
```json
{
  "title": "智能家居产品需求探索",
  "topic": "智能家居控制中心产品概念测试",
  "background": "我们正在开发一款智能家居控制中心，想了解用户对此类产品的期待",
  "research_objectives": [
    "了解用户对智能家居的认知和使用现状",
    "探索用户的核心需求和痛点",
    "测试新产品概念的接受度"
  ]
}
```

**响应**:
```json
{
  "focus_group_id": "fg-12345",
  "title": "智能家居产品需求探索",
  "topic": "智能家居控制中心产品概念测试",
  "status": "draft",
  "participant_count": 0,
  "created_at": "2026-02-18T12:00:00Z"
}
```

##### 2. 添加参与者
```
POST /api/focus-group/{focus_group_id}/participants
```

**请求体**:
```json
{
  "audience_ids": ["aud-001", "aud-002", "...aud-050"]
}
```

**响应**:
```json
{
  "focus_group_id": "fg-12345",
  "added_count": 50,
  "total_participants": 50
}
```

##### 3. 批量生成参与者回答（异步任务）
```
POST /api/focus-group/{focus_group_id}/batch-participant-response
```

**请求体**:
```json
{
  "participant_ids": ["aud-001", "aud-002", "...aud-050"],
  "host_message": "大家好，请问各位目前家里有使用智能设备吗？使用体验如何？"
}
```

**响应**（立即返回任务ID）:
```json
{
  "task_id": "task-abc123",
  "focus_group_id": "fg-12345",
  "is_new_task": true,
  "status": "pending",
  "total_count": 50,
  "created_at": "2026-02-18T12:00:00Z"
}
```

**注意**：如果检测到重复请求（相同 focus_group + 相同参与者 + 相同消息），会直接返回现有任务ID，`is_new_task` 为 `false`。

##### 4. 查询批量任务进度
```
GET /api/focus-group/{focus_group_id}/batch-task/{task_id}
```

**响应**:
```json
{
  "task_id": "task-abc123",
  "focus_group_id": "fg-12345",
  "status": "processing",
  "total_count": 50,
  "completed_count": 38,
  "failed_count": 0,
  "progress_percentage": 76.0,
  "results": [
    {
      "participant_id": "aud-001",
      "success": true,
      "content": "我家里有智能音箱和扫地机器人...",
      "created_at": "2026-02-18T12:00:15Z"
    },
    {
      "participant_id": "aud-002",
      "success": true,
      "content": "目前只有智能灯泡，体验还不错...",
      "created_at": "2026-02-18T12:00:18Z"
    }
  ],
  "created_at": "2026-02-18T12:00:00Z",
  "updated_at": "2026-02-18T12:01:30Z"
}
```

##### 5. 获取活跃批量任务
```
GET /api/focus-group/{focus_group_id}/active-batch-task
```

**响应**:
```json
{
  "has_active_task": true,
  "task_id": "task-abc123",
  "status": "processing",
  "progress_percentage": 76.0
}
```

##### 6. 获取洞察分析
```
GET /api/focus-group/{focus_group_id}/insights
```

**响应**:
```json
{
  "focus_group_id": "fg-12345",
  "total_insights": 45,
  "insights_by_type": {
    "pain_point": [
      {
        "content": "用户普遍反映智能设备之间的互联互通存在问题",
        "confidence_score": 0.92,
        "evidence": [
          "不同品牌的设备无法联动",
          "需要下载多个APP很麻烦"
        ]
      }
    ],
    "need": [
      {
        "content": "用户期望有一个统一的控制中心管理所有智能设备",
        "confidence_score": 0.88,
        "evidence": [
          "希望一个APP就能控制所有设备",
          "最好有语音控制功能"
        ]
      }
    ],
    "preference": [...],
    "behavior": [...]
  },
  "key_themes": [
    "互联互通",
    "易用性",
    "隐私安全"
  ]
}
```

#### 工作流程图

```
客户端                API Server           Agno Workflow          参与者Agents (50个)
   │                     │                      │                      │
   │  批量生成回答(异步)  │                      │                      │
   ├────────────────────>│                      │                      │
   │                     │  创建任务             │                      │
   │                     │  初始化 Workflow     │                      │
   │                     ├─────────────────────>│                      │
   │<────────────────────│                      │                      │
   │  返回 task_id       │                      │                      │
   │                     │                      │                      │
   │                     │                      │  Step 1: 主持人提问  │
   │                     │                      │  (已完成)            │
   │                     │                      │                      │
   │                     │                      │  Step 2: 并行回答    │
   │                     │                      ├─────────────────────>│
   │                     │                      │  (50并发，批次20)    │
   │                     │                      │<─────────────────────│
   │                     │                      │                      │
   │  轮询进度(1-2秒)     │                      │                      │
   ├────────────────────>│                      │                      │
   │                     │  查询进度             │                      │
   │<────────────────────│                      │                      │
   │  38/50 (76%)        │                      │                      │
   │                     │                      │                      │
   │  ...轮询直到完成... │                      │                      │
   │                     │                      │                      │
   │                     │                      │  Step 3: 洞察提取    │
   │                     │                      │  (自动触发)          │
   │                     │                      │                      │
   │  获取洞察           │                      │                      │
   ├────────────────────>│                      │                      │
   │                     │  返回洞察列表         │                      │
   │<────────────────────│                      │                      │
   │  洞察分析结果       │                      │                      │
```

---

### 场景四：受众生成流水线

#### 使用框架
**SmolaAgents - Manager Pattern**

#### 技术选型原因
1. **层级代理架构**：Manager Agent 协调多个专业 Managed Agents
2. **流水线清晰**：基础信息 → 人格特征 → 行为模式，三个独立 Agent 串行执行
3. **工具定义简洁**：使用 `@tool` 装饰器定义生成工具

#### API 端点

##### 1. 生成单个受众画像
```
POST /api/audiences/generate
```

**请求体**:
```json
{
  "description": "35岁左右的互联网产品经理，在一线城市工作，关注效率工具，有创业想法",
  "generation_config": {
    "model": "claude-3-5-sonnet",
    "max_retries": 3
  }
}
```

**响应**:
```json
{
  "audience_id": "aud-12345",
  "name": "张明",
  "demographics": {
    "age": 35,
    "gender": "男",
    "location": "北京",
    "education": "本科",
    "income_level": "20-30万"
  },
  "professional": {
    "industry": "互联网",
    "position": "产品经理",
    "company_size": "500-1000人",
    "work_experience": 8,
    "career_goals": "创业或晋升高级管理岗位"
  },
  "personality": {
    "personality_type": "INTJ",
    "communication_style": "理性分析型，注重数据和逻辑",
    "core_traits": ["追求效率", "注重细节", "独立思考"],
    "key_strengths": ["分析能力强", "目标导向", "善于规划"],
    "key_weaknesses": ["有时过于追求完美", "不善社交"],
    "behavioral_patterns": ["倾向于独立工作", "喜欢深度思考"]
  },
  "lifestyle": {
    "hobbies": ["阅读", "跑步", "科技产品"],
    "values": ["效率", "创新", "专业"],
    "brand_preferences": ["Apple", "Notion", "Tesla"],
    "media_consumption": "主要通过科技博客、播客获取信息",
    "decision_making_style": "理性分析，重视性价比"
  },
  "match_score": 0.92,
  "created_at": "2026-02-18T12:00:00Z"
}
```

##### 2. 批量生成受众（异步任务）
```
POST /api/audiences/batch-generate
```

**请求体**:
```json
{
  "descriptions": [
    "25岁的年轻白领，刚毕业不久，对新事物好奇",
    "40岁的企业高管，注重效率和品质",
    "30岁的全职妈妈，关注家庭和育儿",
    "22岁的大学生，热爱社交和娱乐",
    "45岁的小企业主，务实节俭"
  ],
  "concurrency": 5
}
```

**响应**（立即返回任务ID）:
```json
{
  "task_id": "task-xyz789",
  "status": "pending",
  "total_count": 5,
  "created_at": "2026-02-18T12:00:00Z"
}
```

##### 3. 查询批量生成进度
```
GET /api/audiences/tasks/{task_id}
```

**响应**:
```json
{
  "task_id": "task-xyz789",
  "status": "completed",
  "total_count": 5,
  "completed_count": 5,
  "failed_count": 0,
  "progress_percentage": 100.0,
  "results": [
    {
      "audience_id": "aud-001",
      "name": "李欣",
      "description": "25岁的年轻白领...",
      "match_score": 0.89
    },
    {
      "audience_id": "aud-002",
      "name": "王强",
      "description": "40岁的企业高管...",
      "match_score": 0.91
    }
  ],
  "completed_at": "2026-02-18T12:00:30Z"
}
```

#### 工作流程图

```
客户端               API Server          Manager Agent        Managed Agents
   │                     │                     │                    │
   │  生成受众画像       │                     │                    │
   ├────────────────────>│                     │                    │
   │                     │  初始化流水线       │                    │
   │                     ├────────────────────>│                    │
   │                     │                     │                    │
   │                     │                     │  调用Agent 1:       │
   │                     │                     │  基础信息生成      │
   │                     │                     ├───────────────────>│
   │                     │                     │<───────────────────│
   │                     │                     │  (年龄/性别/职业)  │
   │                     │                     │                    │
   │                     │                     │  调用Agent 2:       │
   │                     │                     │  人格特征生成      │
   │                     │                     ├───────────────────>│
   │                     │                     │<───────────────────│
   │                     │                     │  (MBTI/沟通风格)   │
   │                     │                     │                    │
   │                     │                     │  调用Agent 3:       │
   │                     │                     │  行为模式生成      │
   │                     │                     ├───────────────────>│
   │                     │                     │<───────────────────│
   │                     │                     │  (消费/媒体/决策)  │
   │                     │                     │                    │
   │                     │                     │  整合结果          │
   │                     │<────────────────────│                    │
   │<────────────────────│                     │                    │
   │  完整受众画像       │                     │                    │
```

---

## 技术选型说明

### 为什么场景一用 Claude Agent SDK？

#### 优势
1. **Agentic Loop 天然适配访谈场景**
   - 访谈本质是"提问 → 思考 → 回答 → 追问"的循环
   - Claude Agent SDK 的 Gather → Action → Verify 循环完美匹配

2. **原生 MCP 工具集成**
   - 可以无缝调用 personality（获取人格特征）
   - chat_history（检索历史对话）
   - web_search（搜索实时信息）
   - 无需手动管理工具调用逻辑

3. **上下文记忆自动管理**
   - 无需手动拼接 messages 数组
   - 自动处理上下文截断和压缩

#### 对比其他框架
- **vs Agno**: Agno 更适合并行场景，1对1访谈无需并行
- **vs SmolaAgents**: SmolaAgents 需要手动管理工具和消息历史

---

### 为什么场景二/三用 Agno？

#### 场景二（问卷）- Teams 模式

**优势**:
1. **天然并行能力**
   - `Team.run_parallel()` 一行代码实现100并发
   - 内置并发控制，无需手动管理 Semaphore

2. **Agent 即受众**
   - 每个受众是一个 Agent，概念清晰
   - Team 统一管理，状态追踪简单

3. **结果聚合方便**
   - Team 自动收集所有 Agent 的输出
   - 便于后续统计和分析

#### 场景三（焦点小组）- Workflows 模式

**优势**:
1. **流程清晰**
   - WorkflowStep 1: 主持人提问
   - WorkflowStep 2: 参与者并行回答（内部用 Team）
   - WorkflowStep 3: 洞察提取

2. **步骤可重用**
   - 每轮讨论都是相同的 Workflow 执行
   - 便于实现多轮讨论

3. **状态管理**
   - Workflow 自动维护各步骤状态
   - 便于实现"每3轮提取一次洞察"的逻辑

#### 对比其他框架
- **vs Claude Agent SDK**: 不支持大规模并行
- **vs SmolaAgents**: 并行需要手动用 asyncio.gather，不如 Agno 优雅

---

### 为什么场景四用 SmolaAgents？

#### 优势
1. **Manager Pattern 适配流水线**
   - Manager Agent 协调3个专业 Agent 串行执行
   - 清晰的责任分工

2. **工具定义简洁**
   - `@tool` 装饰器定义生成工具
   - 比 MCP 更轻量，适合简单场景

3. **灵活流程编排**
   - Manager 可以动态决定调用哪些 Agent
   - 支持条件分支（如：如果描述提到职业，则调用职业生成 Agent）

#### 对比其他框架
- **vs Claude Agent SDK**: Agent SDK 更适合交互式场景
- **vs Agno**: Agno Workflows 更适合固定流程，受众生成需要动态编排

---

## 异步任务与轮询机制

### 为什么需要异步任务？

批量场景（场景二/三/四）执行时间较长：
- 问卷投放100人：约1-2分钟
- 焦点小组50人回答：约1-2分钟
- 批量生成50个受众：约2-3分钟

如果使用同步接口，会遇到：
1. **浏览器/代理超时**：Chrome/Cloudflare 约100秒超时
2. **前端无法显示进度**：用户体验差
3. **重复请求问题**：超时后前端重试，导致重复执行

### 异步任务机制

#### 工作流程

```
1. 客户端发起请求
   POST /api/surveys/{survey_id}/deploy
   ↓
2. 服务端立即返回任务ID
   {"task_id": "task-123", "status": "pending"}
   ↓
3. 后台异步执行任务
   任务状态: pending → processing → completed/failed
   ↓
4. 客户端轮询进度
   GET /api/surveys/{survey_id}/tasks/task-123
   每1-2秒查询一次
   ↓
5. 任务完成
   {"status": "completed", "results": [...]}
```

#### 防重复机制

##### 请求指纹
```python
# 基于关键参数生成唯一指纹
fingerprint = MD5(
    focus_group_id +
    participant_ids (排序后) +
    host_message
)
```

##### 活跃任务检查
- 同一个 focus_group 同一时间只能有一个批量任务
- 如果检测到重复请求，直接返回现有任务ID

##### 相同请求返回
```json
{
  "task_id": "task-123",
  "is_new_task": false,  // 表示这是已存在的任务
  "status": "processing",
  "progress_percentage": 65.0
}
```

### 任务生命周期管理

#### 任务状态
- `pending`: 任务已创建，等待执行
- `processing`: 任务正在执行
- `completed`: 任务成功完成
- `failed`: 任务执行失败

#### 任务清理
- 已完成的任务保留**5分钟**后自动清理
- 任务在内存中管理（TaskManager）
- 服务重启后任务状态丢失（已完成的数据已写入数据库）

---

## API调用流程

### 完整用户研究流程示例

```
Step 1: 生成目标受众（场景四）
POST /api/audiences/batch-generate
{
  "descriptions": ["25-35岁城市白领", "30-40岁家庭主妇", ...],
  "concurrency": 10
}
→ 返回 task_id
→ 轮询 GET /api/audiences/tasks/{task_id} 直到完成
→ 获得90个受众画像

Step 2: 问卷初筛（场景二）
POST /api/surveys
{
  "title": "消费习惯筛选问卷",
  "questions": [...]
}
→ 返回 survey_id

POST /api/surveys/{survey_id}/deploy
{
  "audience_ids": [...90个受众...]
}
→ 返回 task_id
→ 轮询进度直到完成
→ GET /api/surveys/{survey_id}/results
→ 筛选出20个高价值受众

Step 3: 焦点小组讨论（场景三）
POST /api/focus-group
{
  "title": "产品需求探索",
  "topic": "...",
  "research_objectives": [...]
}
→ 返回 focus_group_id

POST /api/focus-group/{focus_group_id}/participants
{
  "audience_ids": [...20个高价值受众...]
}
→ 添加参与者

POST /api/focus-group/{focus_group_id}/batch-participant-response
{
  "participant_ids": [...],
  "host_message": "大家有哪些保持健康的习惯？"
}
→ 返回 task_id
→ 轮询进度直到完成
→ 重复此步骤执行4轮讨论

GET /api/focus-group/{focus_group_id}/insights
→ 获取洞察分析

Step 4: 深度访谈（场景一）
POST /api/interviews
{
  "audience_id": "关键参与者ID",
  "topic": "健康消费决策"
}
→ 返回 interview_id

POST /api/interviews/{interview_id}/messages
{
  "message": "您是如何决定购买健康产品的？"
}
→ 获得回答
→ 重复此步骤进行多轮对话

POST /api/interviews/{interview_id}/end
→ 获取访谈摘要和洞察
```

### 前端集成示例

#### 轮询进度（React/Vue通用）

```javascript
// 发起异步任务
const response = await fetch('/api/surveys/{survey_id}/deploy', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ audience_ids })
});
const { task_id } = await response.json();

// 轮询进度
const pollProgress = async () => {
  while (true) {
    const progress = await fetch(`/api/surveys/{survey_id}/tasks/${task_id}`);
    const data = await progress.json();

    // 更新UI进度条
    updateProgressBar(data.progress_percentage);

    if (data.status === 'completed') {
      // 任务完成，获取结果
      const results = await fetch(`/api/surveys/{survey_id}/results`);
      return await results.json();
    } else if (data.status === 'failed') {
      throw new Error('任务失败');
    }

    // 等待1.5秒后继续轮询
    await new Promise(r => setTimeout(r, 1500));
  }
};

const results = await pollProgress();
```

---

## 总结

| 场景 | 框架 | 核心特点 | 适用场景 |
|------|------|---------|---------|
| 1对1访谈 | Claude Agent SDK | Agentic Loop + MCP | 多轮交互、工具调用、上下文记忆 |
| 问卷投放 | Agno Teams | 并行编排、状态管理 | 大规模并发（100-500） |
| 焦点小组 | Agno Workflows | 流程编排、步骤管理 | 固定流程、多阶段执行 |
| 受众生成 | SmolaAgents Manager | 层级代理、流水线 | 串行流程、动态编排 |

所有批量场景均采用**异步任务 + 轮询**机制，避免超时和重复执行问题。
