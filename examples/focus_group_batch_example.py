"""
示例：焦点小组批量执行 - 基于 Agno Framework

演示如何：
1. 创建单个焦点小组讨论
2. 批量执行多个焦点小组（100-200并发支持）
3. 并行收集大量受众回答
4. 进度追踪和结果聚合

场景三：焦点小组批量支持100-200人同时参与焦点小组讨论
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.models import AudienceProfile, FocusGroupStatus
from src.scenarios.focus_group import (
    BatchFocusGroupManager,
    BatchFocusGroupResult,
    FocusGroupFactory
)
from src.workflows.focus_group_workflow import FocusGroupWorkflow, SingleRoundFocusGroup


def create_sample_audience_profiles(count: int = 10) -> List[AudienceProfile]:
    """
    创建示例受众画像列表

    在实际使用中，这些画像应该从数据库获取或由受众生成流水线创建
    """
    profiles = []

    # 定义一些多样化的受众模板
    templates = [
        {
            "demographics": {
                "age": 28,
                "gender": "男",
                "location": "北京",
                "education": "本科",
                "income_level": "中等偏上"
            },
            "professional": {
                "industry": "互联网",
                "position": "产品经理",
                "company_size": "大型企业（500人以上）",
                "work_experience": 5,
                "career_goals": "成为产品总监"
            },
            "personality": {
                "personality_type": "INTJ",
                "communication_style": "直接、逻辑性强",
                "core_traits": ["分析型", "目标导向", "追求效率"],
                "key_strengths": ["战略思维", "问题解决", "数据分析"],
                "key_weaknesses": ["有时过于理性", "不太注重情感沟通"],
                "behavioral_patterns": ["习惯做详细计划", "喜欢用数据支持决策"]
            },
            "lifestyle": {
                "hobbies": ["阅读科技书籍", "跑步", "桌游"],
                "values": ["效率", "创新", "成长"],
                "brand_preferences": ["苹果", "特斯拉", "得到"],
                "media_consumption": "主要通过播客和Newsletter获取信息",
                "decision_making_style": "数据驱动，会做大量对比研究"
            }
        },
        {
            "demographics": {
                "age": 35,
                "gender": "女",
                "location": "上海",
                "education": "硕士",
                "income_level": "高"
            },
            "professional": {
                "industry": "金融",
                "position": "投资经理",
                "company_size": "中型企业（100-500人）",
                "work_experience": 10,
                "career_goals": "成为合伙人"
            },
            "personality": {
                "personality_type": "ENTJ",
                "communication_style": "自信、有说服力",
                "core_traits": ["领导力", "决断力", "竞争意识"],
                "key_strengths": ["商业洞察", "人脉管理", "谈判能力"],
                "key_weaknesses": ["工作压力大", "有时过于强势"],
                "behavioral_patterns": ["注重效率", "喜欢挑战"]
            },
            "lifestyle": {
                "hobbies": ["高尔夫", "红酒品鉴", "艺术收藏"],
                "values": ["成就", "影响力", "品质"],
                "brand_preferences": ["Hermès", "Mercedes-Benz", "Rolex"],
                "media_consumption": "财经媒体、行业报告",
                "decision_making_style": "快速决策，注重投资回报"
            }
        },
        {
            "demographics": {
                "age": 24,
                "gender": "女",
                "location": "深圳",
                "education": "本科",
                "income_level": "中等"
            },
            "professional": {
                "industry": "设计",
                "position": "UI设计师",
                "company_size": "创业公司（50人以下）",
                "work_experience": 2,
                "career_goals": "成为设计主管"
            },
            "personality": {
                "personality_type": "INFP",
                "communication_style": "温和、富有同理心",
                "core_traits": ["创造力", "理想主义", "敏感"],
                "key_strengths": ["审美能力", "用户同理心", "创新思维"],
                "key_weaknesses": ["有时优柔不决", "对批评敏感"],
                "behavioral_patterns": ["喜欢探索新事物", "追求完美"]
            },
            "lifestyle": {
                "hobbies": ["插画", "摄影", "咖啡"],
                "values": ["创意", "美学", "真诚"],
                "brand_preferences": ["无印良品", "宜家", "苹果"],
                "media_consumption": "Dribbble、Behance、小红书",
                "decision_making_style": "感性决策，注重体验和美感"
            }
        },
        {
            "demographics": {
                "age": 42,
                "gender": "男",
                "location": "杭州",
                "education": "MBA",
                "income_level": "高"
            },
            "professional": {
                "industry": "电商",
                "position": "运营总监",
                "company_size": "大型企业（500人以上）",
                "work_experience": 18,
                "career_goals": "创业或成为VP"
            },
            "personality": {
                "personality_type": "ESTP",
                "communication_style": "务实、行动导向",
                "core_traits": ["实用主义", "适应力强", "结果导向"],
                "key_strengths": ["执行力", "危机处理", "资源整合"],
                "key_weaknesses": ["有时缺乏耐心", "不喜欢理论分析"],
                "behavioral_patterns": ["喜欢从实践中学习", "快速响应变化"]
            },
            "lifestyle": {
                "hobbies": ["钓鱼", "自驾游", "美食"],
                "values": ["务实", "家庭", "自由"],
                "brand_preferences": ["华为", "比亚迪", "小米"],
                "media_consumption": "微信公众号、行业社群",
                "decision_making_style": "经验驱动，相信直觉和实践"
            }
        },
        {
            "demographics": {
                "age": 31,
                "gender": "男",
                "location": "成都",
                "education": "硕士",
                "income_level": "中等偏上"
            },
            "professional": {
                "industry": "教育",
                "position": "课程产品经理",
                "company_size": "中型企业（100-500人）",
                "work_experience": 7,
                "career_goals": "成为教育科技领域专家"
            },
            "personality": {
                "personality_type": "ENFJ",
                "communication_style": "热情、有感染力",
                "core_traits": ["利他主义", "有责任感", "善于激励"],
                "key_strengths": ["沟通能力", "团队协作", "用户洞察"],
                "key_weaknesses": ["有时过于理想化", "难以拒绝他人"],
                "behavioral_patterns": ["关注他人需求", "喜欢帮助他人成长"]
            },
            "lifestyle": {
                "hobbies": ["阅读", "户外徒步", "公益活动"],
                "values": ["教育", "成长", "公平"],
                "brand_preferences": ["Kindle", "Notion", "得到"],
                "media_consumption": "知乎、在线课程、播客",
                "decision_making_style": "考虑多方利益，追求共赢方案"
            }
        }
    ]

    # 创建指定数量的受众画像
    for i in range(count):
        template = templates[i % len(templates)]

        # 为每个受众创建独特的ID和名称
        names = ["张明", "李娜", "王芳", "刘强", "陈晨", "赵雪", "周文", "吴磊", "郑洁", "孙涛"]
        name = names[i % len(names)]
        if i >= len(names):
            name = f"{name}_{i // len(names) + 1}"

        profile = AudienceProfile(
            user_id=f"audience_{i + 1}",
            name=name,
            demographics=dict(template["demographics"]),
            professional=dict(template["professional"]),
            personality=dict(template["personality"]),
            lifestyle=dict(template["lifestyle"])
        )

        # 略微调整年龄以增加多样性
        profile.demographics["age"] = template["demographics"]["age"] + (i % 5) - 2

        profiles.append(profile)

    return profiles


async def demo_single_focus_group():
    """演示：单个焦点小组讨论"""

    print("=" * 80)
    print("场景三：焦点小组批量 - Agno Framework 演示")
    print("=" * 80)
    print()

    print("【示例1】单个焦点小组讨论")
    print("-" * 80)
    print()

    # ==================== 1. 创建受众画像 ====================
    print("【步骤1】创建参与者受众画像...")

    participants = create_sample_audience_profiles(5)

    print(f"✓ 创建了 {len(participants)} 个参与者画像")
    for p in participants:
        print(f"  - {p.name}: {p.demographics.get('age')}岁, "
              f"{p.professional.get('position')}, "
              f"{p.personality.get('personality_type')}")
    print()

    # ==================== 2. 定义焦点小组 ====================
    print("【步骤2】创建焦点小组定义...")

    definition = FocusGroupFactory.create_definition(
        topic="移动支付App用户体验",
        audience_profiles=participants,
        questions=[
            "请描述您最近一次使用移动支付时遇到的问题或困惑？",
            "您觉得现有的移动支付App在哪些方面可以改进？",
            "对于移动支付的安全性，您有什么担忧或建议？"
        ],
        background="我们正在研究如何改进移动支付App的用户体验，希望了解不同用户群体的真实使用感受和期望。",
        research_objectives=[
            "了解用户在使用移动支付时的痛点",
            "收集用户对功能改进的建议",
            "评估用户对安全性的关注程度"
        ]
    )

    print(f"✓ 焦点小组定义创建完成")
    print(f"  - 主题: {definition.topic}")
    print(f"  - 参与者: {definition.get_participant_count()} 人")
    print(f"  - 讨论轮数: {definition.max_rounds}")
    print(f"  - 预设问题: {len(definition.questions)} 个")
    print()

    # ==================== 3. 执行焦点小组讨论 ====================
    print("【步骤3】执行焦点小组讨论...")
    print()

    workflow = FocusGroupWorkflow(
        max_concurrency=10,  # 每轮最多10个并发响应
        model_id="claude-3-5-sonnet-20241022"
    )

    print("工作流阶段:")
    print("  → Phase 1: 准备阶段 - 创建主持人和参与者Agent")
    print("  → Phase 2: 讨论阶段 - 多轮问答")
    print("  → Phase 3: 总结阶段 - 提取洞察")
    print()

    print("【执行中】...")
    session = await workflow.run_focus_group(definition)

    # ==================== 4. 展示结果 ====================
    print()
    print("【讨论结果】")
    print(f"  - 会话ID: {session.session_id}")
    print(f"  - 状态: {session.status.value}")
    print(f"  - 总轮数: {len(session.rounds)}")
    print(f"  - 总消息数: {session.total_messages}")
    print()

    if session.status == FocusGroupStatus.COMPLETED:
        print("✅ 焦点小组讨论成功完成！")
        print()

        # 展示每轮讨论
        for round_result in session.rounds:
            print(f"【Round {round_result.round_number}】")
            print(f"  问题: {round_result.host_question[:60]}...")
            print(f"  回答数: {round_result.response_count}")
            print(f"  耗时: {round_result.duration_seconds:.2f}秒")

            # 展示部分回答
            for i, response in enumerate(round_result.responses[:2]):
                participant_name = response.metadata.get("audience_name", "未知")
                print(f"    - {participant_name}: {response.content[:80]}...")
            if round_result.response_count > 2:
                print(f"    ... 还有 {round_result.response_count - 2} 条回答")
            print()

        # 展示洞察
        if session.insights:
            print("【提取的洞察】")
            for i, insight in enumerate(session.insights, 1):
                print(f"  {i}. [{insight.get('type', 'unknown')}] {insight.get('insight', 'N/A')}")
                print(f"     置信度: {insight.get('confidence', 'N/A')}")
            print()
    else:
        print(f"❌ 讨论失败: {session.error_message}")

    print("-" * 80)
    print()


async def demo_batch_focus_groups():
    """演示：批量焦点小组执行"""

    print("【示例2】批量焦点小组执行（100-200并发支持）")
    print("-" * 80)
    print()

    # ==================== 1. 创建多组受众 ====================
    print("【步骤1】创建多组受众画像...")

    # 创建3组不同的受众（每组5人）
    audience_groups = [
        create_sample_audience_profiles(5),  # 组1
        create_sample_audience_profiles(5),  # 组2
        create_sample_audience_profiles(5),  # 组3
    ]

    print(f"✓ 创建了 {len(audience_groups)} 组受众")
    for i, group in enumerate(audience_groups, 1):
        print(f"  - 组{i}: {len(group)} 人")
    print()

    # ==================== 2. 创建批量管理器 ====================
    print("【步骤2】初始化批量焦点小组管理器...")

    batch_manager = BatchFocusGroupManager(
        max_concurrent_groups=50,  # 同时最多50个焦点小组
        max_participants_per_group=20,  # 每组最多20人并发
        model_id="claude-3-5-sonnet-20241022"
    )

    print("✓ 批量管理器初始化完成")
    print(f"  - 最大并发焦点小组: {batch_manager.max_concurrent_groups}")
    print(f"  - 每组最大参与者: {batch_manager.max_participants_per_group}")
    print()

    # ==================== 3. 创建焦点小组定义 ====================
    print("【步骤3】使用工厂批量创建焦点小组定义...")

    definitions = FocusGroupFactory.create_multiple_definitions(
        topic="新能源汽车购买决策",
        audience_groups=audience_groups,
        questions=[
            "您在考虑购买新能源汽车时，最看重哪些因素？",
            "您对新能源汽车的续航里程有什么期望？"
        ],
        background="研究消费者对新能源汽车的购买决策因素",
        research_objectives=[
            "了解不同群体的购买考量",
            "评估续航里程的重要性"
        ]
    )

    print(f"✓ 创建了 {len(definitions)} 个焦点小组定义")
    for i, defn in enumerate(definitions, 1):
        print(f"  - 小组{i}: {defn.title}, {defn.get_participant_count()}人")
    print()

    # ==================== 4. 执行批量焦点小组 ====================
    print("【步骤4】执行批量焦点小组...")
    print()

    print("【执行中】并发运行所有焦点小组...")
    result = await batch_manager.run_batch(definitions)

    # ==================== 5. 展示批量结果 ====================
    print()
    print("【批量执行结果】")
    print(f"  - 批次ID: {result.batch_id}")
    print(f"  - 总焦点小组数: {result.total_groups}")
    print(f"  - 成功: {result.successful_groups}")
    print(f"  - 失败: {result.failed_groups}")
    print(f"  - 成功率: {result.success_rate:.1f}%")
    print(f"  - 总执行时间: {result.execution_time_seconds:.2f}秒")
    print()

    if result.sessions:
        print("【各焦点小组详情】")
        for i, session in enumerate(result.sessions, 1):
            status_icon = "✅" if session.status == FocusGroupStatus.COMPLETED else "❌"
            print(f"  {status_icon} 小组{i}: {session.status.value}, "
                  f"{len(session.rounds)}轮, {session.total_messages}条消息")
            if session.insights:
                print(f"     洞察: {len(session.insights)}条")
        print()

    if result.errors:
        print("【错误信息】")
        for error in result.errors:
            print(f"  - {error}")
        print()

    print("-" * 80)
    print()


async def demo_parallel_response_collection():
    """演示：并行收集大量受众回答"""

    print("【示例3】并行收集大量受众回答（高并发模式）")
    print("-" * 80)
    print()

    # ==================== 1. 创建大量受众 ====================
    print("【步骤1】创建大量受众画像（模拟100-200人场景）...")

    # 在演示中使用20人模拟，实际可扩展到200人
    audience_profiles = create_sample_audience_profiles(20)

    print(f"✓ 创建了 {len(audience_profiles)} 个受众画像")
    print()

    # ==================== 2. 单问题并行收集 ====================
    print("【步骤2】并行收集单个问题的回答...")

    batch_manager = BatchFocusGroupManager(
        max_concurrent_groups=50,
        model_id="claude-3-5-sonnet-20241022"
    )

    question = "您认为AI技术会如何改变您的日常工作？请分享您的看法和担忧。"

    print(f"【问题】{question}")
    print()

    print("【执行中】并行收集所有受众回答...")
    responses = await batch_manager.run_parallel_response_collection(
        question=question,
        audience_profiles=audience_profiles,
        topic="AI技术对工作的影响",
        background="研究不同职业背景人群对AI的看法"
    )

    # ==================== 3. 展示收集结果 ====================
    print()
    print("【收集结果】")
    print(f"  - 总受众数: {len(audience_profiles)}")
    print(f"  - 成功回答: {len(responses)}")
    print(f"  - 收集率: {len(responses)/len(audience_profiles)*100:.1f}%")
    print()

    if responses:
        print("【部分回答展示】")
        for i, resp in enumerate(responses[:5], 1):
            name = resp.get("audience_name", "未知")
            content = resp.get("response", "")[:100]
            time_sec = resp.get("response_time_seconds", 0)
            print(f"  {i}. {name}: {content}...")
            print(f"     响应时间: {time_sec:.2f}秒")

        if len(responses) > 5:
            print(f"  ... 还有 {len(responses) - 5} 条回答")
        print()

    print("-" * 80)
    print()


async def demo_single_round_focus_group():
    """演示：单轮焦点小组（简化接口）"""

    print("【示例4】单轮焦点小组讨论（简化接口）")
    print("-" * 80)
    print()

    # ==================== 1. 创建受众 ====================
    print("【步骤1】创建参与者...")

    participants = create_sample_audience_profiles(8)

    print(f"✓ 创建了 {len(participants)} 个参与者")
    print()

    # ==================== 2. 使用简化接口 ====================
    print("【步骤2】使用 SingleRoundFocusGroup 简化接口...")

    single_round = SingleRoundFocusGroup(
        max_concurrency=20,
        model_id="claude-3-5-sonnet-20241022"
    )

    question = "如果您可以改变一个当前工作中的流程或工具，您会选择什么？为什么？"

    print(f"【问题】{question}")
    print()

    # ==================== 3. 收集回答 ====================
    print("【执行中】收集所有参与者回答...")

    messages = await single_round.ask_question(
        question=question,
        audience_profiles=participants,
        topic="工作效率改进",
        background="探索提高工作效率的方向"
    )

    # ==================== 4. 展示结果 ====================
    print()
    print("【收集结果】")
    print(f"  - 参与者: {len(participants)}")
    print(f"  - 回答数: {len(messages)}")
    print()

    if messages:
        print("【回答内容】")
        for i, msg in enumerate(messages, 1):
            name = msg.metadata.get("audience_name", "未知")
            print(f"  {i}. [{name}]")
            print(f"     {msg.content[:120]}...")
            print()

    print("-" * 80)
    print()


async def main():
    """主函数：运行所有演示"""

    # 检查环境变量
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("⚠️  警告: 未设置 ANTHROPIC_API_KEY 或 OPENROUTER_API_KEY 环境变量")
        print()
        print("请运行以下命令之一：")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        print("  export OPENROUTER_API_KEY='your-api-key'")
        print()
        print("【演示模式】以下展示预期的执行流程（不实际调用API）...")
        print()
        demonstrate_expected_flow()
        return

    # ==================== 运行演示 ====================
    try:
        # 示例1: 单个焦点小组讨论
        await demo_single_focus_group()

        # 示例2: 批量焦点小组执行
        await demo_batch_focus_groups()

        # 示例3: 并行收集大量受众回答
        await demo_parallel_response_collection()

        # 示例4: 单轮焦点小组（简化接口）
        await demo_single_round_focus_group()

        print("=" * 80)
        print("所有演示完成！")
        print("=" * 80)

    except Exception as e:
        print(f"❌ 演示执行出错: {str(e)}")
        import traceback
        traceback.print_exc()


def demonstrate_expected_flow():
    """演示模式：展示预期的执行流程（不实际调用API）"""

    print("【模拟执行流程】")
    print()
    print("=" * 80)
    print("场景三：焦点小组批量 - Agno Framework 演示（模拟）")
    print("=" * 80)
    print()

    print("【架构概述】")
    print("-" * 80)
    print()
    print("┌─────────────────────────────────────────────────────────┐")
    print("│              BatchFocusGroupManager                     │")
    print("│                    (批量管理器)                          │")
    print("│  - 支持100-200并发焦点小组                               │")
    print("│  - 错误隔离、进度追踪                                    │")
    print("└───────────────────────┬─────────────────────────────────┘")
    print("                        │")
    print("                        ▼")
    print("┌─────────────────────────────────────────────────────────┐")
    print("│              FocusGroupWorkflow                         │")
    print("│                    (工作流编排)                          │")
    print("│  Phase 1: 准备阶段 - 创建Agent                          │")
    print("│  Phase 2: 讨论阶段 - 多轮问答                            │")
    print("│  Phase 3: 总结阶段 - 提取洞察                            │")
    print("└───────────────────────┬─────────────────────────────────┘")
    print("                        │")
    print("        ┌───────────────┴───────────────┐")
    print("        ▼                               ▼")
    print("┌─────────────────┐           ┌─────────────────┐")
    print("│ ModeratorAgent  │           │ ParticipantAgent│")
    print("│   (主持人)       │           │   (参与者)       │")
    print("│ - 生成问题       │           │ - 基于画像回答   │")
    print("│ - 总结讨论       │           │ - 保持人设一致   │")
    print("│ - 提取洞察       │           │ - 真实性表达     │")
    print("└─────────────────┘           └─────────────────┘")
    print()

    print("【示例流程】")
    print("-" * 80)
    print()

    print("1️⃣  单个焦点小组讨论:")
    print("   输入: 5个受众画像 + 3个讨论问题 + 研究目标")
    print("   ↓")
    print("   FocusGroupWorkflow 执行:")
    print("   → Phase 1: 创建1个ModeratorAgent + 5个ParticipantAgent")
    print("   → Phase 2: 3轮讨论（主持人提问 → 参与者并发回答 → 主持人总结）")
    print("   → Phase 3: 从所有讨论中提取洞察")
    print("   ↓")
    print("   输出: FocusGroupSession（包含所有轮次回答和洞察）")
    print()

    print("2️⃣  批量焦点小组执行:")
    print("   创建3组受众（每组5人）→ 使用FocusGroupFactory创建3个定义")
    print("   ↓")
    print("   BatchFocusGroupManager 并发执行:")
    print("   - 最大并发焦点小组: 50")
    print("   - 每组内参与者并发: 20")
    print("   - 任务防重复、错误隔离")
    print("   ↓")
    print("   输出: BatchFocusGroupResult（聚合所有小组结果）")
    print()

    print("3️⃣  并行收集大量回答:")
    print("   输入: 100-200个受众画像 + 1个问题")
    print("   ↓")
    print("   run_parallel_response_collection 高并发执行:")
    print("   - 不分组，直接并发收集")
    print("   - 使用ConcurrencyManager控制并发")
    print("   ↓")
    print("   输出: List[Dict]（每个受众的回答）")
    print()

    print("4️⃣  单轮焦点小组（简化接口）:")
    print("   输入: 受众画像 + 单个问题")
    print("   ↓")
    print("   SingleRoundFocusGroup.ask_question:")
    print("   - 跳过主持人逻辑")
    print("   - 直接并发收集回答")
    print("   ↓")
    print("   输出: List[FocusGroupMessage]")
    print()

    print("-" * 80)
    print()

    print("【核心特性】")
    print("✓ Agno Agent 架构: 使用 agno.Agent 实现参与者和主持人")
    print("✓ 对话风格指南: 真实性、情感表达、具体性、矛盾性（模拟真人）")
    print("✓ SPIN问题框架: 主持人使用Situation-Problem-Implication-Need-payoff")
    print("✓ 并发控制: ConcurrencyManager + Semaphore 限流")
    print("✓ 任务管理: TaskManager 防重复、进度追踪")
    print("✓ 错误隔离: 单个参与者失败不影响整体")
    print("✓ 批量执行: 支持100-200并发焦点小组")
    print()

    print("【数据模型】")
    print("✓ AudienceProfile: 受众画像（demographics, professional, personality, lifestyle）")
    print("✓ FocusGroupDefinition: 焦点小组定义（主题、问题、参与者、研究目标）")
    print("✓ FocusGroupSession: 会话结果（轮次、消息、洞察）")
    print("✓ BatchFocusGroupResult: 批量执行结果（成功率、执行时间）")
    print()

    print("【并发能力】")
    print("✓ 焦点小组级并发: 50个（DEFAULT_MAX_CONCURRENT_GROUPS）")
    print("✓ 参与者级并发: 20个（DEFAULT_MAX_PARTICIPANTS_PER_GROUP）")
    print("✓ 总并发理论上限: 50 × 20 = 1000 并发Agent调用")
    print("✓ 实际受限于API限流，建议根据实际配额调整")
    print()

    print("【实际运行】")
    print("设置API密钥后，脚本会:")
    print("1. 调用Claude API执行真实的焦点小组讨论")
    print("2. 展示完整的讨论过程和结果")
    print("3. 提取并展示研究洞察")
    print("4. 统计执行成功率和耗时")
    print()


if __name__ == "__main__":
    asyncio.run(main())
