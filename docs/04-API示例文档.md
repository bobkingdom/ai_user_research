# Siry AI Research - API 示例文档

## 1. 场景一：1对1受众访谈（Claude Agent SDK）

### 1.1 基础使用示例

```python
import asyncio
from src.scenarios.interview import InterviewAgent
from src.core.models import AudienceProfile

# 准备受众数据
audience_data = {
    "user_id": "aud-001",
    "name": "张明",
    "age": 35,
    "gender": "男",
    "position": "产品经理",
    "work_experience": 8,
    "company_size": "500-1000人",
    "location": "北京",
    "industry": "互联网",
    "education": "本科",
    "income_level": "20-30万",
    "personality_type": "INTJ",
    "communication_style": "直接、逻辑性强",
    "hobbies": ["阅读", "跑步", "科技产品"],
    "values": ["效率", "创新", "专业"],
}

personality_data = {
    "personality_type": "INTJ",
    "communication_style": "理性分析型，注重数据和逻辑",
    "core_traits": ["追求效率", "注重细节", "独立思考"],
    "key_strengths": ["分析能力强", "目标导向", "善于规划"],
    "key_weaknesses": ["有时过于追求完美", "不善社交"],
    "behavioral_patterns": ["倾向于独立工作", "喜欢深度思考"],
}

# 创建访谈代理
async def run_interview():
    agent = InterviewAgent(
        audience_profile=AudienceProfile.from_dict(audience_data),
        personality_data=personality_data,
        mcp_tools=["web_search", "memory_store"],
    )

    # 启动访谈
    opening = await agent.start_interview(
        topic="效率工具使用体验",
        research_objectives=["了解日常工作痛点", "探索工具选择标准"]
    )
    print(f"开场白: {opening}")

    # 多轮对话
    response1 = await agent.respond("您平时工作中最常用的效率工具是什么？")
    print(f"回答1: {response1.content}")

    response2 = await agent.respond("使用这些工具时遇到过什么困难吗？")
    print(f"回答2: {response2.content}")

    # 结束访谈
    summary = await agent.end_interview()
    print(f"访谈摘要: {summary}")

    return summary

# 执行
asyncio.run(run_interview())
```

### 1.2 带 MCP 工具的访谈

```python
from src.scenarios.interview import InterviewAgent, MCPToolConfig

# 配置 MCP 工具
mcp_config = MCPToolConfig(
    tools=[
        {
            "name": "web_search",
            "description": "搜索市场最新信息",
            "enabled": True,
        },
        {
            "name": "memory_store",
            "description": "存储关键洞察",
            "enabled": True,
        },
        {
            "name": "note_take",
            "description": "记录访谈要点",
            "enabled": True,
        },
    ]
)

async def interview_with_tools():
    agent = InterviewAgent(
        audience_profile=audience_profile,
        mcp_config=mcp_config,
        interview_config={
            "max_rounds": 20,
            "timeout": 3600,
            "auto_followup": True,
        }
    )

    # 访谈过程中，Agent 会自动决定何时使用工具
    response = await agent.respond(
        "您对市场上的竞品了解多少？有什么看法？"
    )

    # 检查是否使用了工具
    if response.tools_used:
        print(f"使用的工具: {response.tools_used}")

    return response

asyncio.run(interview_with_tools())
```

### 1.3 访谈结果处理

```python
async def process_interview_results():
    agent = InterviewAgent(audience_profile=audience_profile)

    # ... 执行访谈 ...

    summary = await agent.end_interview()

    # 获取完整访谈记录
    transcript = summary.messages
    print(f"访谈轮数: {len(transcript)}")

    # 获取提取的洞察
    insights = summary.insights
    for insight in insights:
        print(f"洞察: {insight.content}")
        print(f"类型: {insight.insight_type}")
        print(f"置信度: {insight.confidence_score}")

    # 获取情感变化曲线
    emotion_curve = summary.emotion_timeline
    print(f"情感变化: {emotion_curve}")

    return summary
```

---

## 2. 场景二：问卷批量投放（Agno）

### 2.1 基础批量投放

```python
import asyncio
from src.scenarios.survey import SurveyDeployment
from src.core.models import SurveyDefinition, AudienceProfile

# 定义问卷
survey = SurveyDefinition(
    survey_id="survey-001",
    title="产品满意度调查",
    questions=[
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
        },
    ]
)

# 准备受众列表（示例：100个受众）
audiences = [
    AudienceProfile(
        user_id=f"aud-{i:03d}",
        name=f"用户{i}",
        age=25 + (i % 30),
        gender="男" if i % 2 == 0 else "女",
        industry="互联网" if i % 3 == 0 else "金融",
        # ... 其他字段
    )
    for i in range(100)
]

async def deploy_survey():
    deployment = SurveyDeployment(
        survey=survey,
        concurrency_config={
            "max_concurrency": 100,
            "batch_size": 50,
        }
    )

    # 执行批量投放
    result = await deployment.deploy(audiences=audiences)

    print(f"总数: {result.total_count}")
    print(f"成功: {result.success_count}")
    print(f"失败: {result.failed_count}")

    return result

asyncio.run(deploy_survey())
```

### 2.2 带进度追踪的投放

```python
async def deploy_with_progress():
    deployment = SurveyDeployment(survey=survey)

    # 使用回调追踪进度
    async def on_progress(current, total, result):
        print(f"进度: {current}/{total} ({current/total*100:.1f}%)")
        if not result.success:
            print(f"  失败: {result.audience_id} - {result.error}")

    result = await deployment.deploy(
        audiences=audiences,
        on_progress=on_progress,
    )

    return result

# 或使用轮询模式（推荐用于前端集成）
async def deploy_with_polling():
    deployment = SurveyDeployment(survey=survey)

    # 创建任务
    task = await deployment.create_task(audiences=audiences)
    print(f"任务ID: {task.task_id}")

    # 轮询进度
    while True:
        progress = await deployment.get_progress(task.task_id)
        print(f"进度: {progress.completed}/{progress.total}")

        if progress.status in ["completed", "failed"]:
            break

        await asyncio.sleep(1.5)  # 轮询间隔

    # 获取结果
    result = await deployment.get_result(task.task_id)
    return result
```

### 2.3 结果聚合分析

```python
from src.scenarios.survey import SurveyAggregator

async def analyze_results():
    deployment = SurveyDeployment(survey=survey)
    result = await deployment.deploy(audiences=audiences)

    # 聚合分析
    aggregator = SurveyAggregator(result)

    # 选择题统计
    q1_stats = aggregator.get_choice_statistics("q1")
    print("Q1 满意度分布:")
    for option, count in q1_stats.items():
        print(f"  {option}: {count} ({count/result.success_count*100:.1f}%)")

    # 多选题统计
    q2_stats = aggregator.get_multiple_choice_statistics("q2")
    print("Q2 特性偏好:")
    for option, count in q2_stats.items():
        print(f"  {option}: {count}")

    # 开放题文本聚类
    q3_clusters = aggregator.cluster_open_responses("q3", n_clusters=5)
    print("Q3 痛点聚类:")
    for cluster in q3_clusters:
        print(f"  主题: {cluster.theme}")
        print(f"  样例: {cluster.examples[:3]}")

    # 生成汇总报告
    report = aggregator.generate_report()
    print(f"报告:\n{report}")

    return report
```

---

## 3. 场景三：焦点小组批量（Agno）

### 3.1 创建焦点小组

```python
import asyncio
from src.scenarios.focus_group import FocusGroupSession
from src.core.models import FocusGroupDefinition, AudienceProfile

# 定义焦点小组
focus_group = FocusGroupDefinition(
    focus_group_id="fg-001",
    title="新产品概念测试",
    topic="智能家居产品需求探索",
    background="我们正在开发一款智能家居控制中心，想了解用户对此类产品的期待",
    research_objectives=[
        "了解用户对智能家居的认知和使用现状",
        "探索用户的核心需求和痛点",
        "测试新产品概念的接受度",
    ],
)

# 准备参与者（示例：50个参与者）
participants = [
    AudienceProfile(
        user_id=f"part-{i:03d}",
        name=f"参与者{i}",
        age=28 + (i % 20),
        # ... 其他字段
    )
    for i in range(50)
]

async def create_focus_group():
    session = FocusGroupSession(
        definition=focus_group,
        workflow_config={
            "max_concurrency": 50,
            "batch_size": 20,
            "insight_extraction_interval": 3,  # 每3轮提取一次洞察
        }
    )

    # 添加参与者
    participant_ids = await session.add_participants(participants)
    print(f"添加了 {len(participant_ids)} 个参与者")

    return session
```

### 3.2 执行焦点小组讨论

```python
async def run_focus_group_discussion():
    session = await create_focus_group()

    # 自动生成 SPIN 问题框架
    questions = await session.generate_spin_questions()
    print(f"生成了 {len(questions)} 个问题")

    # 逐轮执行讨论
    for i, question in enumerate(questions):
        print(f"\n=== 第 {i+1} 轮 ===")
        print(f"主持人: {question.content}")

        # 执行一轮讨论（所有参与者并行回答）
        round_result = await session.run_round(question.content)

        # 输出部分回答
        for response in round_result.responses[:3]:
            print(f"  {response.participant_name}: {response.content[:100]}...")

        # 检查是否有提取的洞察
        if round_result.insights:
            print(f"  [洞察] {len(round_result.insights)} 条新洞察")

    # 获取讨论摘要
    summary = await session.get_summary()
    return summary
```

### 3.3 批量生成参与者回答（带轮询）

```python
async def batch_generate_with_polling():
    session = await create_focus_group()

    host_message = "大家好，今天我们讨论智能家居产品。请问各位目前家里有使用智能设备吗？使用体验如何？"

    # 创建批量任务
    task = await session.create_batch_task(
        participant_ids=[p.user_id for p in participants],
        host_message=host_message,
    )

    print(f"任务创建成功: {task.task_id}")
    print(f"查询进度URL: /batch-task/{task.task_id}")

    # 轮询进度
    while True:
        progress = await session.get_task_progress(task.task_id)

        print(f"进度: {progress.completed_count}/{progress.total_count} "
              f"({progress.progress_percentage:.1f}%)")

        if progress.status == "completed":
            print("任务完成!")
            break
        elif progress.status == "failed":
            print(f"任务失败: {progress.error_message}")
            break

        await asyncio.sleep(1.5)

    # 获取所有回答
    results = progress.results
    for r in results[:5]:
        if r.success:
            print(f"  {r.participant_id}: {r.content[:80]}...")
        else:
            print(f"  {r.participant_id}: 失败 - {r.error}")

    return results
```

### 3.4 洞察提取

```python
from src.scenarios.focus_group import InsightExtractor

async def extract_insights():
    session = await create_focus_group()

    # ... 执行讨论 ...

    # 手动触发洞察提取
    extractor = InsightExtractor(session)
    insights = await extractor.extract(
        recent_messages_count=20,
        insight_types=["pain_point", "need", "preference", "behavior"],
        confidence_threshold=0.7,
        max_insights=10,
    )

    print(f"提取了 {len(insights)} 条洞察:")
    for insight in insights:
        print(f"  [{insight.insight_type}] {insight.content}")
        print(f"    置信度: {insight.confidence_score}")
        print(f"    证据: {insight.evidence[:2]}")

    return insights
```

---

## 4. 场景四：受众生成流水线（SmolaAgents）

### 4.1 基础受众生成

```python
import asyncio
from src.scenarios.generation import AudienceGenerationPipeline

async def generate_audience():
    pipeline = AudienceGenerationPipeline(
        generation_config={
            "max_retries": 3,
            "model": "claude-3-5-sonnet",
        }
    )

    # 从描述生成受众画像
    description = "35岁左右的互联网产品经理，在一线城市工作，关注效率工具，有创业想法"

    audience = await pipeline.generate(description)

    print("生成的受众画像:")
    print(f"  姓名: {audience.name}")
    print(f"  年龄: {audience.demographics.age}")
    print(f"  职位: {audience.professional.position}")
    print(f"  性格类型: {audience.personality.personality_type}")
    print(f"  核心特质: {audience.personality.core_traits}")
    print(f"  兴趣爱好: {audience.lifestyle.hobbies}")

    return audience

asyncio.run(generate_audience())
```

### 4.2 批量受众生成

```python
async def batch_generate_audiences():
    pipeline = AudienceGenerationPipeline()

    descriptions = [
        "25岁的年轻白领，刚毕业不久，对新事物好奇",
        "40岁的企业高管，注重效率和品质",
        "30岁的全职妈妈，关注家庭和育儿",
        "22岁的大学生，热爱社交和娱乐",
        "45岁的小企业主，务实节俭",
    ]

    audiences = await pipeline.batch_generate(
        descriptions=descriptions,
        concurrency=5,
    )

    for i, audience in enumerate(audiences):
        print(f"\n受众 {i+1}: {audience.name}")
        print(f"  描述匹配度: {audience.match_score}")

    return audiences
```

### 4.3 自定义生成流程

```python
from src.scenarios.generation import (
    AudienceGenerationPipeline,
    BasicInfoAgent,
    PersonalityAgent,
    BehaviorAgent,
)

async def custom_generation():
    # 创建自定义 Agent
    basic_agent = BasicInfoAgent(
        model="claude-3-5-sonnet",
        constraints={
            "age_range": (25, 45),
            "locations": ["北京", "上海", "深圳", "杭州"],
        }
    )

    personality_agent = PersonalityAgent(
        model="claude-3-5-sonnet",
        personality_framework="MBTI",  # 或 "Big Five"
    )

    behavior_agent = BehaviorAgent(
        model="claude-3-5-sonnet",
        focus_areas=["消费习惯", "媒体使用", "决策风格"],
    )

    # 组装流水线
    pipeline = AudienceGenerationPipeline(
        basic_agent=basic_agent,
        personality_agent=personality_agent,
        behavior_agent=behavior_agent,
    )

    audience = await pipeline.generate(
        "科技行业的中高层管理者，注重家庭与工作平衡"
    )

    return audience
```

### 4.4 生成结果验证

```python
from src.scenarios.generation import AudienceValidator

async def validate_generated_audience():
    pipeline = AudienceGenerationPipeline()
    audience = await pipeline.generate("30岁的互联网从业者")

    # 验证生成结果
    validator = AudienceValidator()
    validation_result = validator.validate(audience)

    print(f"验证结果: {'通过' if validation_result.is_valid else '失败'}")

    if not validation_result.is_valid:
        print("问题:")
        for issue in validation_result.issues:
            print(f"  - {issue}")

    # 一致性检查
    consistency_score = validator.check_consistency(audience)
    print(f"一致性得分: {consistency_score:.2f}")

    return audience if validation_result.is_valid else None
```

---

## 5. 通用功能示例

### 5.1 配置管理

```python
from src.core.config import FrameworkConfig, ScenarioConfig

# 加载配置
config = FrameworkConfig()
print(f"Claude API Key: {config.claude_api_key[:10]}...")
print(f"默认模型: {config.claude_model}")

# 场景配置
scenario_config = ScenarioConfig()
print(f"问卷最大并发: {scenario_config.survey_max_concurrency}")
print(f"焦点小组批次大小: {scenario_config.focus_group_batch_size}")
```

### 5.2 错误处理

```python
from src.utils.error_handler import ErrorHandler, with_retry

# 使用重试装饰器
@with_retry(max_retries=3, base_delay=1.0)
async def risky_operation():
    # 可能失败的操作
    pass

# 使用错误处理器
handler = ErrorHandler()

async def safe_execution():
    result = await handler.with_retry(
        func=some_async_function,
        args=(arg1, arg2),
        on_error=lambda e: print(f"错误: {e}"),
    )
    return result
```

### 5.3 并发控制

```python
from src.utils.concurrency import ConcurrencyManager

async def controlled_batch_execution():
    manager = ConcurrencyManager(max_concurrency=100)

    tasks = [
        lambda: process_item(i)
        for i in range(500)
    ]

    results = await manager.execute_batch(
        tasks=tasks,
        batch_size=50,
        on_batch_complete=lambda batch_num: print(f"批次 {batch_num} 完成"),
    )

    return results
```

### 5.4 提示词模板

```python
from src.core.prompts import PromptTemplateManager

# 加载模板
PromptTemplateManager.load_templates("templates/")

# 渲染模板
system_prompt = PromptTemplateManager.render(
    template_key="audience_system",
    context={
        "name": "张明",
        "age": 35,
        "position": "产品经理",
        # ... 其他字段
    }
)

print(f"生成的提示词长度: {len(system_prompt)}")
```

---

## 6. 完整应用示例

### 6.1 端到端市场调研流程

```python
import asyncio
from src.scenarios.interview import InterviewAgent
from src.scenarios.survey import SurveyDeployment
from src.scenarios.focus_group import FocusGroupSession
from src.scenarios.generation import AudienceGenerationPipeline

async def full_research_workflow():
    """完整的市场调研流程示例"""

    # Step 1: 生成目标受众
    print("=== Step 1: 生成受众画像 ===")
    pipeline = AudienceGenerationPipeline()
    audiences = await pipeline.batch_generate(
        descriptions=[
            "25-35岁的城市白领，关注健康生活",
            "30-40岁的家庭主妇，重视家庭质量",
            "20-30岁的年轻人，追求时尚潮流",
        ] * 30,  # 生成90个受众
        concurrency=10,
    )
    print(f"生成了 {len(audiences)} 个受众")

    # Step 2: 问卷初筛
    print("\n=== Step 2: 问卷初筛 ===")
    screening_survey = SurveyDefinition(
        survey_id="screening-001",
        title="消费习惯筛选问卷",
        questions=[
            {
                "id": "q1",
                "type": "single_choice",
                "content": "您每月在健康产品上的支出大约是？",
                "options": ["500元以下", "500-1000元", "1000-2000元", "2000元以上"]
            },
        ]
    )

    deployment = SurveyDeployment(survey=screening_survey)
    survey_result = await deployment.deploy(audiences=audiences)

    # 筛选高价值受众
    high_value_audiences = [
        r.audience for r in survey_result.results
        if r.answers.get("q1") in ["1000-2000元", "2000元以上"]
    ]
    print(f"筛选出 {len(high_value_audiences)} 个高价值受众")

    # Step 3: 焦点小组深度讨论
    print("\n=== Step 3: 焦点小组讨论 ===")
    focus_group = FocusGroupDefinition(
        focus_group_id="fg-research-001",
        title="健康产品需求探索",
        topic="健康生活方式与产品选择",
        research_objectives=["了解健康消费动机", "探索未满足需求"],
    )

    session = FocusGroupSession(definition=focus_group)
    await session.add_participants(high_value_audiences[:20])  # 选20人

    discussion_topics = [
        "大家平时都有哪些保持健康的习惯？",
        "在选择健康产品时，最看重什么因素？",
        "有没有遇到过让你失望的健康产品？为什么失望？",
        "理想中的健康产品应该是什么样的？",
    ]

    for topic in discussion_topics:
        round_result = await session.run_round(topic)
        print(f"话题: {topic[:20]}... - {len(round_result.responses)} 条回复")

    # 获取洞察
    insights = await session.get_summary()
    print(f"提取了 {len(insights.key_insights)} 条关键洞察")

    # Step 4: 1对1深度访谈（针对关键人物）
    print("\n=== Step 4: 深度访谈 ===")
    key_participant = high_value_audiences[0]

    interview_agent = InterviewAgent(
        audience_profile=key_participant,
        mcp_tools=["web_search", "memory_store"],
    )

    await interview_agent.start_interview(topic="健康消费决策")

    interview_questions = [
        "能详细说说您是如何决定购买一款健康产品的吗？",
        "您提到了XX因素很重要，能举个具体例子吗？",
        "如果我们开发一款新产品，您最希望它解决什么问题？",
    ]

    for q in interview_questions:
        response = await interview_agent.respond(q)
        print(f"Q: {q[:30]}...")
        print(f"A: {response.content[:100]}...")

    interview_summary = await interview_agent.end_interview()

    # 汇总所有研究结果
    print("\n=== 研究完成 ===")
    return {
        "audiences_generated": len(audiences),
        "survey_responses": survey_result.success_count,
        "high_value_segment": len(high_value_audiences),
        "focus_group_participants": 20,
        "key_insights": insights.key_insights,
        "interview_highlights": interview_summary.insights,
    }

# 执行完整流程
if __name__ == "__main__":
    result = asyncio.run(full_research_workflow())
    print(f"\n最终结果: {result}")
```

---

## 7. 与 backhour_ai 的对比

### 7.1 1对1访谈对比

```python
# backhour_ai 原实现（DSPy + SmolaAgents）
from services.audience_agent import AudienceAgent as OldAgent

old_agent = OldAgent(
    audience_data=audience_data,
    personality_data=personality_data,
    engine="S",  # SmolaAgents
)
response = await old_agent.chat("你好")

# siry_ai_research 新实现（Claude Agent SDK）
from src.scenarios.interview import InterviewAgent as NewAgent

new_agent = NewAgent(
    audience_profile=audience_profile,
    mcp_tools=["web_search"],
)
response = await new_agent.respond("你好")
```

### 7.2 批量生成对比

```python
# backhour_ai 原实现（asyncio.gather + dspy.Parallel）
# focus_group_router.py:962-1000
async def old_batch_generate():
    if participant_count >= 3:
        # 使用 dspy.Parallel
        results = batch_generate_focus_group_responses_parallel(...)
    else:
        # 使用 asyncio.gather
        results = await asyncio.gather(*tasks)

# siry_ai_research 新实现（Agno Team.run_parallel）
from src.scenarios.focus_group import FocusGroupSession

session = FocusGroupSession(definition=focus_group)
results = await session.run_round(host_message)  # 内部使用 Agno
```

---

## 附录：数据模型参考

### AudienceProfile

```python
@dataclass
class AudienceProfile:
    user_id: str
    name: str

    # 人口统计
    demographics: Demographics  # age, gender, location, education, income_level

    # 职业信息
    professional: Professional  # industry, position, company_size, work_experience

    # 人格特征
    personality: Personality  # personality_type, communication_style, core_traits

    # 生活方式
    lifestyle: Lifestyle  # hobbies, values, brand_preferences, media_consumption
```

### SurveyDefinition

```python
@dataclass
class SurveyDefinition:
    survey_id: str
    title: str
    questions: List[Question]

@dataclass
class Question:
    id: str
    type: str  # single_choice, multiple_choice, open_ended
    content: str
    options: Optional[List[str]] = None
    max_length: Optional[int] = None
```

### FocusGroupDefinition

```python
@dataclass
class FocusGroupDefinition:
    focus_group_id: str
    title: str
    topic: str
    background: Optional[str] = None
    research_objectives: List[str] = field(default_factory=list)
    questions_json: Optional[List[Dict]] = None
```
