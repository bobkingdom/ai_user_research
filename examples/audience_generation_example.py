"""
示例：使用SmolaAgents流水线进行受众画像生成

演示如何：
1. 单个受众生成
2. 批量受众生成
3. 多分群受众生成
4. 进度追踪和错误处理
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipelines.audience_generation_pipeline import AudienceGenerationPipeline
from src.pipelines.batch_generation import (
    BatchAudienceGenerator,
    create_segment_from_description,
    print_generation_summary
)


async def demo_single_generation():
    """演示：单个受众生成"""

    print("=" * 80)
    print("场景四：受众生成流水线 - SmolaAgents 演示")
    print("=" * 80)
    print()

    print("【示例1】单个受众画像生成")
    print("-" * 80)
    print()

    # ==================== 1. 创建生成流水线 ====================
    print("【步骤1】初始化受众生成流水线...")

    pipeline = AudienceGenerationPipeline(
        model_id="anthropic/claude-3-5-sonnet-20241022",
        max_steps=15
    )

    print("✓ 流水线初始化完成")
    print("  - Manager Agent: 负责协调生成流程")
    print("  - Managed Agents: 5个专业Agent（demographics, personality, lifestyle, validator, merger）")
    print()

    # ==================== 2. 生成受众画像 ====================
    print("【步骤2】生成受众画像...")
    print()

    # 受众描述
    description = """
35岁左右的互联网产品经理，在一线城市工作。
有8-10年的工作经验，目前在中大型互联网公司担任高级产品经理。
希望晋升为产品总监，拓展战略规划能力。
性格偏INTJ型，理性、逻辑清晰、追求效率。
喜欢阅读科技类书籍、跑步、围棋，注重工作生活平衡。
"""

    print(f"【受众描述】")
    print(description.strip())
    print()

    print("【生成中】三步流水线执行中...")
    print("  → Step 1: 生成基础信息（demographics + professional）")
    print("  → Step 2: 生成人格特征（personality）")
    print("  → Step 3: 生成生活方式（lifestyle）")
    print("  → Step 4: 整合数据")
    print("  → Step 5: 验证数据质量")
    print()

    # 执行生成
    result = await pipeline.generate_audience_profile(
        description=description,
        name="李明"
    )

    # ==================== 3. 展示结果 ====================
    if result["success"]:
        profile = result["profile"]

        print("✅ 受众画像生成成功！")
        print()
        print("【生成结果】")
        print(f"姓名: {profile.name}")
        print(f"用户ID: {profile.user_id}")
        print()

        print("【基础信息】")
        demo = profile.demographics
        print(f"  年龄: {demo.get('age', 'N/A')}")
        print(f"  性别: {demo.get('gender', 'N/A')}")
        print(f"  地区: {demo.get('location', 'N/A')}")
        print(f"  教育: {demo.get('education', 'N/A')}")
        print(f"  收入水平: {demo.get('income_level', 'N/A')}")
        print()

        print("【职业信息】")
        prof = profile.professional
        print(f"  行业: {prof.get('industry', 'N/A')}")
        print(f"  职位: {prof.get('position', 'N/A')}")
        print(f"  公司规模: {prof.get('company_size', 'N/A')}")
        print(f"  工作年限: {prof.get('work_experience', 'N/A')}年")
        print(f"  职业目标: {prof.get('career_goals', 'N/A')}")
        print()

        print("【人格特征】")
        pers = profile.personality
        print(f"  人格类型: {pers.get('personality_type', 'N/A')}")
        print(f"  沟通风格: {pers.get('communication_style', 'N/A')}")
        print(f"  核心特质: {', '.join(pers.get('core_traits', []))}")
        print(f"  主要优势: {', '.join(pers.get('key_strengths', []))}")
        print(f"  注意劣势: {', '.join(pers.get('key_weaknesses', []))}")
        print()

        print("【生活方式】")
        life = profile.lifestyle
        print(f"  兴趣爱好: {', '.join(life.get('hobbies', []))}")
        print(f"  核心价值观: {', '.join(life.get('values', []))}")
        print(f"  品牌偏好: {', '.join(life.get('brand_preferences', []))}")
        print(f"  媒体偏好: {life.get('media_consumption', 'N/A')}")
        print(f"  决策风格: {life.get('decision_making_style', 'N/A')}")
        print()

    else:
        print(f"❌ 生成失败: {result['error_message']}")
        if result["validation_errors"]:
            print(f"验证错误: {result['validation_errors']}")
        print()

    print("-" * 80)
    print()


async def demo_batch_generation():
    """演示：批量受众生成"""

    print("【示例2】批量受众画像生成")
    print("-" * 80)
    print()

    # ==================== 1. 创建批量生成管理器 ====================
    print("【步骤1】初始化批量生成管理器...")

    batch_generator = BatchAudienceGenerator(
        model_id="anthropic/claude-3-5-sonnet-20241022",
        max_concurrency=3,  # 控制并发数
        retry_config={
            "max_retries": 3,
            "retry_delay": 1.0,
            "exponential_backoff": True
        }
    )

    print("✓ 批量生成管理器初始化完成")
    print("  - 最大并发数: 3")
    print("  - 重试策略: 最多3次，指数退避")
    print()

    # ==================== 2. 定义受众分群 ====================
    print("【步骤2】定义目标受众分群...")

    segment = create_segment_from_description(
        name="互联网产品经理群体",
        description="30-40岁的互联网产品经理，5-10年工作经验，在一二线城市工作",
        target_count=5,  # 生成5个受众
        demographics={
            "age_range": "30-40",
            "industry": "互联网",
            "position_level": "中高级"
        }
    )

    print(f"✓ 受众分群创建完成")
    print(f"  - 分群名称: {segment.name}")
    print(f"  - 目标数量: {segment.target_count}")
    print(f"  - 描述: {segment.description}")
    print()

    # ==================== 3. 执行批量生成 ====================
    print("【步骤3】执行批量生成...")
    print()

    # 进度回调函数
    def progress_callback(current, total, profile):
        """打印生成进度"""
        percentage = (current / total) * 100
        print(f"  进度: [{current}/{total}] {percentage:.1f}% - 已生成 {profile.name}")

    # 执行批量生成
    task = await batch_generator.generate_batch(
        segment=segment,
        progress_callback=progress_callback
    )

    print()

    # ==================== 4. 展示结果摘要 ====================
    print_generation_summary(task)

    # 详细展示前3个生成的受众
    if task.generated_profiles:
        print("📝 生成受众详情（前3个）:")
        print()

        for i, profile in enumerate(task.generated_profiles[:3]):
            print(f"[受众 {i+1}] {profile.name}")
            print(f"  基础信息:")
            print(f"    - 年龄: {profile.demographics.get('age', 'N/A')}")
            print(f"    - 性别: {profile.demographics.get('gender', 'N/A')}")
            print(f"    - 地区: {profile.demographics.get('location', 'N/A')}")

            print(f"  职业信息:")
            print(f"    - 职位: {profile.professional.get('position', 'N/A')}")
            print(f"    - 工作年限: {profile.professional.get('work_experience', 'N/A')}年")

            print(f"  人格特征:")
            print(f"    - 类型: {profile.personality.get('personality_type', 'N/A')}")

            print(f"  生活方式:")
            hobbies = ', '.join(profile.lifestyle.get('hobbies', [])[:3])
            print(f"    - 兴趣: {hobbies}")
            print()

    print("-" * 80)
    print()


async def demo_multiple_segments():
    """演示：多分群受众生成"""

    print("【示例3】多分群受众生成")
    print("-" * 80)
    print()

    # ==================== 1. 定义多个受众分群 ====================
    print("【步骤1】定义多个目标受众分群...")

    segments = [
        create_segment_from_description(
            name="年轻创业者",
            description="25-30岁的创业者，刚创立公司1-3年，在一线城市",
            target_count=3
        ),
        create_segment_from_description(
            name="资深设计师",
            description="35-45岁的资深UI/UX设计师，10年以上经验，在大厂工作",
            target_count=3
        ),
        create_segment_from_description(
            name="技术管理者",
            description="30-40岁的技术经理或架构师，带领团队5-20人",
            target_count=3
        )
    ]

    print(f"✓ 创建了 {len(segments)} 个受众分群")
    for seg in segments:
        print(f"  - {seg.name}: 目标生成 {seg.target_count} 个")
    print()

    # ==================== 2. 执行多分群生成 ====================
    print("【步骤2】执行多分群批量生成...")
    print()

    batch_generator = BatchAudienceGenerator(
        model_id="anthropic/claude-3-5-sonnet-20241022",
        max_concurrency=2
    )

    # 进度回调
    def progress_callback(current, total, profile):
        print(f"  [{current}/{total}] 生成完成: {profile.name}")

    # 生成所有分群
    tasks = await batch_generator.generate_multiple_segments(
        segments=segments,
        progress_callback=progress_callback
    )

    print()

    # ==================== 3. 展示统计结果 ====================
    print("【生成统计】")
    print("=" * 60)

    total_target = sum(task.segment.target_count for task in tasks)
    total_generated = sum(len(task.generated_profiles) for task in tasks)
    success_rate = (total_generated / total_target * 100) if total_target > 0 else 0

    print(f"总目标数量: {total_target}")
    print(f"实际生成数: {total_generated}")
    print(f"成功率: {success_rate:.1f}%")
    print()

    for task in tasks:
        print(f"分群: {task.segment.name}")
        print(f"  - 状态: {task.status.value}")
        print(f"  - 进度: {task.progress_percentage:.1f}%")
        print(f"  - 生成数: {len(task.generated_profiles)}/{task.segment.target_count}")
        if task.error_message:
            print(f"  - 错误: {task.error_message}")

    print("=" * 60)
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
        # 示例1: 单个受众生成
        await demo_single_generation()

        # 示例2: 批量受众生成
        await demo_batch_generation()

        # 示例3: 多分群受众生成
        await demo_multiple_segments()

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
    print("场景四：受众生成流水线 - SmolaAgents 演示（模拟）")
    print("=" * 80)
    print()

    print("【示例流程】")
    print("-" * 80)
    print()

    print("1️⃣ 单个受众生成:")
    print("   输入: '35岁左右的互联网产品经理，在一线城市工作...'")
    print("   ↓")
    print("   Manager Agent 协调流水线:")
    print("   → demographics_generator: 生成基础信息和职业背景")
    print("   → personality_generator: 生成人格特征（基于基础信息）")
    print("   → lifestyle_generator: 生成生活方式（基于人格特征）")
    print("   → data_merger: 整合三部分数据")
    print("   → profile_validator: 验证数据质量")
    print("   ↓")
    print("   输出: 完整的 AudienceProfile 对象")
    print()

    print("2️⃣ 批量受众生成:")
    print("   创建 AudienceSegment: '互联网产品经理群体'")
    print("   目标数量: 5个")
    print("   ↓")
    print("   BatchAudienceGenerator 并发执行:")
    print("   - 最大并发数: 3")
    print("   - 错误重试: 最多3次，指数退避")
    print("   - 进度追踪: 实时回调进度")
    print("   ↓")
    print("   输出: GenerationTask（包含5个 AudienceProfile）")
    print()

    print("3️⃣ 多分群生成:")
    print("   创建3个分群: 年轻创业者、资深设计师、技术管理者")
    print("   ↓")
    print("   顺序执行各分群批量生成")
    print("   ↓")
    print("   输出: List[GenerationTask]（3个任务结果）")
    print()

    print("-" * 80)
    print()

    print("【关键特性】")
    print("✓ Manager + Managed Agents 架构: 清晰的职责分离")
    print("✓ 三步流水线: 基础信息 → 人格特征 → 生活方式")
    print("✓ 自动验证: 确保数据完整性和一致性")
    print("✓ 并发控制: 避免API限流")
    print("✓ 错误处理: 重试机制 + 失败隔离")
    print("✓ 进度追踪: 实时反馈生成进度")
    print()

    print("【数据模型】")
    print("✓ AudienceSegment: 受众分群定义")
    print("✓ GenerationTask: 生成任务状态和结果")
    print("✓ AudienceProfile: 完整受众画像")
    print()

    print("【实际运行】")
    print("设置API密钥后，脚本会:")
    print("1. 调用Claude API生成真实的受众画像")
    print("2. 展示完整的生成过程和结果")
    print("3. 统计生成成功率和耗时")
    print()


if __name__ == "__main__":
    asyncio.run(main())
