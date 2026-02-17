"""
示例：使用InterviewAgent进行1对1受众访谈

演示如何：
1. 创建受众画像
2. 配置访谈参数
3. 启动访谈会话
4. 进行多轮对话
5. 提取用户洞察
6. 生成访谈总结
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scenarios.interview.agent import InterviewAgent
from src.scenarios.interview.models import (
    AudienceProfileForInterview,
    InterviewConfig,
)


async def main():
    """主函数：演示完整的访谈流程"""

    print("=" * 80)
    print("场景一：1对1受众访谈 - Claude Agent SDK 演示")
    print("=" * 80)
    print()

    # ==================== 1. 创建受众画像 ====================
    print("【步骤1】创建受众画像...")

    audience_profile = AudienceProfileForInterview(
        user_id="demo-user-001",
        name="李明",

        # 基础信息
        age=32,
        gender="男",
        location="北京",
        education="硕士",
        income_level="中高",
        marital_status="已婚",

        # 职业信息
        industry="互联网",
        position="产品经理",
        company_size="500-1000人",
        work_experience=8,
        career_goals="希望晋升为产品总监，拓展战略规划能力",

        # 人格特征
        personality_type="INTJ (建筑师)",
        communication_style="逻辑清晰，偏好数据驱动的讨论",
        core_traits=["理性思考", "目标导向", "追求效率"],
        key_strengths=["战略规划", "数据分析", "项目管理"],
        key_weaknesses=["有时过于理性", "缺乏情感表达"],
        behavioral_patterns=["喜欢提前规划", "重视时间管理", "倾向独立工作"],

        # 生活方式
        hobbies=["阅读科技类书籍", "跑步", "围棋"],
        values=["创新", "效率", "持续学习"],
        brand_preferences=["Apple", "Tesla", "MUJI"],
        leisure_activities=["周末郊游", "参加行业meetup"],
        media_consumption="主要通过微信公众号、知乎、得到App获取信息",
        decision_making_style="理性分析，重视ROI",
        risk_tolerance="中等偏保守",
        social_style="内向型，小圈子社交",
        life_attitudes="工作生活平衡，注重个人成长",
    )

    print(f"✓ 受众画像创建完成: {audience_profile.name}")
    print(f"  - 职业: {audience_profile.position} @ {audience_profile.industry}")
    print(f"  - 性格类型: {audience_profile.personality_type}")
    print()

    # ==================== 2. 配置访谈参数 ====================
    print("【步骤2】配置访谈参数...")

    interview_config = InterviewConfig(
        research_topic="职场人士的时间管理痛点和需求",
        research_objectives=[
            "了解产品经理群体的日常时间分配情况",
            "识别时间管理中的核心痛点和挑战",
            "探索对时间管理工具的需求和期望",
            "理解影响工作效率的关键因素",
        ],
        max_rounds=20,
        timeout_seconds=3600,
        enable_mcp_tools=False,  # 演示中先不启用MCP工具
        auto_extract_insights=True,
        model_id="claude-3-5-sonnet-20241022",
    )

    print(f"✓ 访谈配置完成")
    print(f"  - 研究主题: {interview_config.research_topic}")
    print(f"  - 研究目标: {len(interview_config.research_objectives)}个")
    print(f"  - 最大轮数: {interview_config.max_rounds}")
    print()

    # ==================== 3. 检查API密钥 ====================
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  警告: 未设置 ANTHROPIC_API_KEY 环境变量")
        print("   请运行: export ANTHROPIC_API_KEY='your-api-key'")
        print()
        print("【演示模式】以下展示预期的交互流程（不实际调用API）...")
        print()

        # 模拟访谈流程演示
        demonstrate_interview_flow(audience_profile, interview_config)
        return

    # ==================== 4. 创建InterviewAgent ====================
    print("【步骤3】初始化InterviewAgent...")

    agent = InterviewAgent(
        audience_profile=audience_profile,
        interview_config=interview_config,
        mcp_tools=None,  # 可选：传入MCP工具定义
        api_key=api_key,
    )

    print(f"✓ Agent初始化完成")
    print()

    # ==================== 5. 启动访谈 ====================
    print("【步骤4】启动访谈会话...")
    print("-" * 80)

    session = await agent.start_interview()

    print(f"\n✓ 会话已启动 (ID: {session.session_id})")
    print(f"\n【AI受众回应】")
    print(session.messages[-1].content)
    print("-" * 80)
    print()

    # ==================== 6. 进行多轮对话 ====================
    print("【步骤5】进行多轮访谈对话...")
    print()

    # SPIN框架的问题序列
    interview_questions = [
        # S - Situation (现状探索)
        "能否先介绍一下你平时一天的工作内容和时间安排？",

        # P - Problem (问题识别)
        "在日常工作中，你觉得时间管理上最大的挑战是什么？",

        # I - Implication (影响探究)
        "这些时间管理的问题对你的工作效率和生活质量有什么影响？",

        # N - Need-payoff (需求确认)
        "如果有一个工具能帮你更好地管理时间，你最希望它具备哪些功能？",
    ]

    for i, question in enumerate(interview_questions, 1):
        print(f"【问题 {i}/{len(interview_questions)}】")
        print(f"研究员: {question}")
        print()

        # 获取AI受众的回复
        response = await agent.respond(question)

        print(f"【AI受众回应】")
        print(response.content)

        # 如果有提取到洞察
        if response.insights:
            print(f"\n💡 自动提取洞察 ({len(response.insights)}条):")
            for insight in response.insights:
                print(f"   - [{insight.insight_type}] {insight.content}")

        print("-" * 80)
        print()

    # ==================== 7. 结束访谈 ====================
    print("【步骤6】结束访谈，生成总结...")

    summary = await agent.end_interview()

    print(f"\n✓ 访谈已结束")
    print()
    print("【访谈总结】")
    print(f"  - 会话ID: {summary.session_id}")
    print(f"  - 总消息数: {summary.total_messages}")
    print(f"  - 提取洞察: {summary.total_insights}条")
    print(f"  - 持续时间: {summary.duration_seconds}秒")
    print()

    print("【洞察统计】")
    for insight_type, count in summary.insights_by_type.items():
        print(f"  - {insight_type}: {count}条")
    print()

    print("【关键发现】")
    for finding in summary.key_findings:
        print(f"  - {finding}")
    print()

    # ==================== 8. 导出结果（可选） ====================
    print("【步骤7】导出访谈结果（可选）...")

    # 可以将结果保存为JSON
    import json
    output_file = f"interview_result_{session.session_id[:8]}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "session_id": summary.session_id,
                "audience": audience_profile.to_dict(),
                "config": interview_config.model_dump(),
                "total_messages": summary.total_messages,
                "total_insights": summary.total_insights,
                "duration_seconds": summary.duration_seconds,
                "insights_by_type": summary.insights_by_type,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                    }
                    for msg in summary.messages
                ],
                "insights": [
                    {
                        "content": ins.content,
                        "type": ins.insight_type,
                        "confidence": ins.confidence_score,
                        "evidence": ins.evidence,
                    }
                    for ins in summary.insights
                ],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"✓ 结果已保存到: {output_file}")
    print()

    print("=" * 80)
    print("访谈演示完成！")
    print("=" * 80)


def demonstrate_interview_flow(profile, config):
    """演示模式：展示预期的交互流程（不实际调用API）"""

    print("【模拟访谈流程】")
    print()
    print("-" * 80)
    print("【研究员】能否先介绍一下你平时一天的工作内容和时间安排？")
    print()
    print("【AI受众 - 李明】")
    print("好的。我目前是一名产品经理，每天的工作确实挺紧凑的。通常早上9点到公司，")
    print("先花半小时查看邮件和各个工作群的消息，了解有没有紧急事项。")
    print()
    print("上午主要是各种会议，比如项目进度同步会、需求评审会等，基本上10点到12点")
    print("都被会议占满了。午休后下午1点半开始，我会尽量安排一些需要专注的工作，")
    print("比如撰写PRD文档、分析数据报告什么的。但实际上经常被临时会议打断...")
    print("-" * 80)
    print()

    print("【模拟洞察提取】")
    print("💡 自动提取洞察:")
    print("   - [behavior] 工作日程被会议占据大部分时间")
    print("   - [pain_point] 专注工作时间经常被临时会议打断")
    print()

    print("【说明】")
    print("在实际运行中，InterviewAgent会：")
    print("1. 根据受众画像生成个性化的回答")
    print("2. 遵循SPIN框架逐步深入探索")
    print("3. 自动提取用户洞察（痛点、需求、行为等）")
    print("4. 支持MCP工具调用（如搜索、数据查询）")
    print("5. 生成完整的访谈总结报告")
    print()


if __name__ == "__main__":
    asyncio.run(main())
