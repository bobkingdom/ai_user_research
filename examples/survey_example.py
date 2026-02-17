"""
问卷批量投放示例 - 演示如何使用 Agno Teams 实现 100-500 并发问卷投放

本示例演示：
1. 创建问卷定义（SurveyDefinition）
2. 准备目标受众列表（AudienceProfile）
3. 使用 SurveyDeployment 批量投放问卷
4. 获取并分析投放结果（DeploymentResult）

运行方式：
    python examples/survey_example.py

环境变量：
    ANTHROPIC_API_KEY: 必需，用于调用 Claude API
    SURVEY_MAX_CONCURRENCY: 可选，默认100
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.models import (
    QuestionType,
    SurveyQuestion,
    SurveyDefinition,
    AudienceProfile
)
from src.workflows.survey_deployment import SurveyDeployment

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_survey() -> SurveyDefinition:
    """创建示例问卷：关于工作方式偏好的调研"""
    questions = [
        SurveyQuestion(
            question_id="q1",
            question_text="您更喜欢哪种工作方式？",
            question_type=QuestionType.SINGLE_CHOICE,
            options=["远程办公", "混合办公", "现场办公"],
            required=True
        ),
        SurveyQuestion(
            question_id="q2",
            question_text="您在工作中最看重以下哪些因素？（可多选）",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["薪资待遇", "工作氛围", "职业发展", "工作生活平衡", "公司文化"],
            required=True
        ),
        SurveyQuestion(
            question_id="q3",
            question_text="请为您目前的工作满意度打分（1-5分）",
            question_type=QuestionType.RATING,
            required=True
        ),
        SurveyQuestion(
            question_id="q4",
            question_text="您认为理想的工作环境应该具备哪些特点？",
            question_type=QuestionType.TEXT,
            required=False
        ),
    ]
    
    return SurveyDefinition(
        survey_id="survey_work_preference_2024",
        title="工作方式偏好调研",
        description="了解职场人士对工作方式和环境的偏好",
        questions=questions,
        target_audience_count=100,
        created_at=datetime.now()
    )


def create_sample_audiences(count: int = 100) -> list[AudienceProfile]:
    """
    创建示例受众列表
    
    实际场景中，这些数据应该来自：
    - 数据库中的受众画像数据
    - Scene 4（受众生成流水线）生成的合成受众
    """
    audiences = []
    
    # 示例：创建多样化的受众画像
    industries = ["科技", "金融", "教育", "医疗", "制造"]
    positions = ["工程师", "产品经理", "设计师", "数据分析师", "运营专员"]
    personality_types = ["INTJ", "ENFP", "ISTJ", "ESFJ", "INTP"]
    
    for i in range(count):
        audience = AudienceProfile(
            user_id=f"user_{i+1:04d}",
            name=f"测试用户{i+1}",
            demographics={
                "age": 25 + (i % 20),
                "gender": "男" if i % 2 == 0 else "女",
                "location": "北京" if i % 3 == 0 else "上海" if i % 3 == 1 else "深圳",
                "education": "本科" if i % 4 < 3 else "硕士",
                "income_level": "10-20万" if i % 3 == 0 else "20-40万" if i % 3 == 1 else "40万以上"
            },
            professional={
                "industry": industries[i % len(industries)],
                "position": positions[i % len(positions)],
                "company_size": "50-200人" if i % 3 == 0 else "200-1000人" if i % 3 == 1 else "1000人以上",
                "work_experience": 2 + (i % 10),
                "career_goals": "技术专家" if i % 2 == 0 else "管理层"
            },
            personality={
                "personality_type": personality_types[i % len(personality_types)],
                "communication_style": "直接" if i % 2 == 0 else "委婉",
                "core_traits": ["理性", "高效"] if i % 2 == 0 else ["感性", "细致"],
                "key_strengths": ["逻辑思维", "执行力"],
                "key_weaknesses": ["过于追求完美"] if i % 2 == 0 else ["容易分心"],
                "behavioral_patterns": ["注重细节", "目标导向"]
            },
            lifestyle={
                "hobbies": ["阅读", "运动"] if i % 2 == 0 else ["音乐", "旅行"],
                "values": ["成长", "创新", "平衡"],
                "brand_preferences": ["Apple", "Nike"] if i % 2 == 0 else ["华为", "小米"],
                "media_consumption": "视频为主" if i % 2 == 0 else "图文为主",
                "decision_making_style": "理性分析" if i % 2 == 0 else "直觉决策"
            }
        )
        audiences.append(audience)
    
    return audiences


async def main():
    """主函数：演示问卷批量投放流程"""
    
    # 检查必需的 API Key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("❌ 缺少 ANTHROPIC_API_KEY 环境变量")
        logger.info("💡 请设置: export ANTHROPIC_API_KEY=your_api_key_here")
        return
    
    logger.info("=" * 80)
    logger.info("问卷批量投放示例 - Agno Teams 实现")
    logger.info("=" * 80)
    
    # Step 1: 创建问卷
    logger.info("\n📝 Step 1: 创建示例问卷")
    survey = create_sample_survey()
    logger.info(f"问卷ID: {survey.survey_id}")
    logger.info(f"问卷标题: {survey.title}")
    logger.info(f"问题数量: {len(survey.questions)}")
    
    # Step 2: 准备受众列表
    logger.info("\n👥 Step 2: 准备目标受众列表")
    # 可以通过命令行参数调整受众数量
    audience_count = int(os.getenv("AUDIENCE_COUNT", "100"))
    audiences = create_sample_audiences(count=audience_count)
    logger.info(f"目标受众数量: {len(audiences)}")
    
    # Step 3: 创建 SurveyDeployment 编排器
    logger.info("\n⚙️ Step 3: 初始化 SurveyDeployment 编排器")
    max_concurrency = int(os.getenv("SURVEY_MAX_CONCURRENCY", "100"))
    deployment = SurveyDeployment(
        max_concurrency=max_concurrency,
        model_id="claude-3-5-sonnet-20241022"
    )
    logger.info(f"最大并发数: {max_concurrency}")
    
    # Step 4: 执行批量投放
    logger.info("\n🚀 Step 4: 开始批量投放问卷")
    logger.info(f"预计处理 {len(audiences)} 个受众，最大并发 {max_concurrency}")
    
    start_time = datetime.now()
    result = await deployment.deploy(
        survey=survey,
        audience_list=audiences,
        task_id="example_task_001"
    )
    end_time = datetime.now()
    
    # Step 5: 输出结果统计
    logger.info("\n" + "=" * 80)
    logger.info("📊 投放结果统计")
    logger.info("=" * 80)
    logger.info(f"任务ID: {result.task_id}")
    logger.info(f"问卷ID: {result.survey_id}")
    logger.info(f"目标受众总数: {result.total_audiences}")
    logger.info(f"成功回答数: {result.successful_responses}")
    logger.info(f"失败回答数: {result.failed_responses}")
    logger.info(f"成功率: {result.success_rate:.1f}%")
    logger.info(f"执行耗时: {result.execution_time_seconds:.2f} 秒")
    logger.info(f"平均每受众耗时: {result.execution_time_seconds/len(audiences):.2f} 秒")
    
    # Step 6: 展示部分回答示例
    if result.responses:
        logger.info("\n📋 回答示例（前3个）：")
        for i, response in enumerate(result.responses[:3], 1):
            logger.info(f"\n受众 {i}: {response.audience_profile.name}")
            logger.info(f"  - User ID: {response.audience_profile.user_id}")
            logger.info(f"  - 回答数量: {len(response.answers)} 个问题")
            logger.info(f"  - 完成时间: {response.completion_time_seconds:.2f} 秒")
            
            # 展示部分答案
            for qid, answer in list(response.answers.items())[:2]:
                logger.info(f"  - {qid}: {answer}")
    
    # Step 7: 展示错误信息（如果有）
    if result.errors:
        logger.info("\n⚠️ 错误列表：")
        for error in result.errors[:5]:  # 只展示前5个错误
            logger.info(f"  - 受众 {error.get('audience_name')}: {error.get('error')}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ 示例执行完成")
    logger.info("=" * 80)
    
    # 返回结果供进一步分析
    return result


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
