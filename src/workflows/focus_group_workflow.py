"""
焦点小组工作流 - 基于 Agno Teams
支持多轮焦点小组讨论，100-200并发参与者
"""

import logging
import asyncio
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.models import (
    FocusGroupDefinition,
    FocusGroupSession,
    FocusGroupRoundResult,
    FocusGroupMessage,
    FocusGroupStatus,
    FocusGroupParticipant,
    AudienceProfile,
    ParticipantRole
)
from src.agents.focus_group_agent import FocusGroupParticipantAgent, FocusGroupModeratorAgent
from src.utils.concurrency import ConcurrencyManager
from src.utils.task_manager import TaskManager, TaskStatus

logger = logging.getLogger(__name__)


class FocusGroupWorkflow:
    """
    焦点小组工作流编排器

    架构：
    - 使用 Agno Teams 管理多个 ParticipantAgent
    - 使用 ConcurrencyManager 控制并发
    - 使用 TaskManager 防止重复任务
    - 支持多轮讨论

    工作流程：
    Phase 1: 准备阶段 - 创建主持人和参与者Agent
    Phase 2: 讨论阶段 - 多轮提问和回答
    Phase 3: 总结阶段 - 提取洞察
    """

    def __init__(
        self,
        max_concurrency: Optional[int] = None,
        model_id: str = "claude-3-5-sonnet-20241022"
    ):
        """
        初始化焦点小组工作流

        Args:
            max_concurrency: 最大并发数，默认使用 ConcurrencyManager.FOCUS_GROUP_MAX_CONCURRENCY
            model_id: 使用的模型ID
        """
        self.concurrency_manager = ConcurrencyManager.for_focus_group()
        if max_concurrency:
            self.concurrency_manager.max_concurrency = max_concurrency

        self.task_manager = TaskManager()
        self.model_id = model_id

        logger.info(
            f"FocusGroupWorkflow 初始化: max_concurrency={self.concurrency_manager.max_concurrency}, "
            f"model={model_id}"
        )

    async def run_focus_group(
        self,
        definition: FocusGroupDefinition,
        session_id: Optional[str] = None
    ) -> FocusGroupSession:
        """
        执行焦点小组讨论

        流程：
        1. 创建会话和任务
        2. Phase 1: 准备阶段 - 创建Agent
        3. Phase 2: 讨论阶段 - 多轮讨论
        4. Phase 3: 总结阶段 - 提取洞察

        Args:
            definition: 焦点小组定义
            session_id: 可选的会话ID

        Returns:
            FocusGroupSession: 完整的焦点小组会话结果
        """
        start_time = datetime.now()

        # 创建会话
        if not session_id:
            session_id = str(uuid.uuid4())

        session = FocusGroupSession(
            session_id=session_id,
            definition=definition
        )

        logger.info(
            f"🚀 开始焦点小组讨论 - Session: {session_id}, "
            f"Topic: {definition.topic}, Participants: {definition.get_participant_count()}"
        )

        # 创建任务（防重复）
        task_params = {
            "focus_group_id": definition.focus_group_id,
            "participant_ids": [p.participant_id for p in definition.participants],
            "task_type": "focus_group"
        }

        existing_task, is_new = await self.task_manager.get_or_create_task(
            task_key=f"focus_group_{definition.focus_group_id}",
            task_params=task_params,
            total_count=definition.max_rounds * definition.get_participant_count()
        )

        if not is_new:
            logger.warning(f"焦点小组任务已存在，返回当前状态")
            session.status = FocusGroupStatus.ACTIVE
            return session

        try:
            # 开始任务
            await self.task_manager.start_task(existing_task.task_id)
            session.start()

            # Phase 1: 准备阶段 - 创建Agent
            logger.info("📋 Phase 1: 准备阶段 - 创建Agent")
            moderator, participant_agents = await self._prepare_agents(definition)

            # Phase 2: 讨论阶段 - 多轮讨论
            logger.info("💬 Phase 2: 讨论阶段")
            await self._execute_discussion(
                session=session,
                moderator=moderator,
                participant_agents=participant_agents,
                task_id=existing_task.task_id
            )

            # Phase 3: 总结阶段 - 提取洞察
            logger.info("📊 Phase 3: 总结阶段 - 提取洞察")
            insights = await self._extract_insights(session, moderator)

            # 完成会话
            session.complete(insights)

            # 更新任务状态
            await self.task_manager.complete_task(existing_task.task_id, success=True)

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"✅ 焦点小组讨论完成 - Session: {session_id}, "
                f"Rounds: {len(session.rounds)}, Messages: {session.total_messages}, "
                f"Insights: {len(insights)}, Time: {execution_time:.2f}s"
            )

            return session

        except Exception as e:
            logger.error(f"❌ 焦点小组讨论失败 - Session: {session_id}, Error: {str(e)}")

            # 更新状态
            session.fail(str(e))
            await self.task_manager.complete_task(
                existing_task.task_id,
                success=False,
                error_message=str(e)
            )

            return session

    async def _prepare_agents(
        self,
        definition: FocusGroupDefinition
    ) -> tuple[FocusGroupModeratorAgent, Dict[str, FocusGroupParticipantAgent]]:
        """
        准备阶段：创建主持人和参与者Agent

        Args:
            definition: 焦点小组定义

        Returns:
            (moderator, {participant_id: agent}) 元组
        """
        # 创建主持人Agent
        moderator = FocusGroupModeratorAgent(
            focus_group=definition,
            model_id=self.model_id
        )

        # 创建参与者Agent字典
        participant_agents = {}

        for participant in definition.participants:
            if participant.role == ParticipantRole.PARTICIPANT:
                agent = FocusGroupParticipantAgent(
                    audience_profile=participant.audience_profile,
                    focus_group=definition,
                    model_id=self.model_id
                )
                participant_agents[participant.participant_id] = agent

        logger.info(
            f"准备阶段完成: 1 主持人, {len(participant_agents)} 参与者"
        )

        return moderator, participant_agents

    async def _execute_discussion(
        self,
        session: FocusGroupSession,
        moderator: FocusGroupModeratorAgent,
        participant_agents: Dict[str, FocusGroupParticipantAgent],
        task_id: str
    ) -> None:
        """
        讨论阶段：执行多轮讨论

        Args:
            session: 会话对象
            moderator: 主持人Agent
            participant_agents: 参与者Agent字典
            task_id: 任务ID
        """
        definition = session.definition
        previous_summary = None

        for round_number in range(1, definition.max_rounds + 1):
            logger.info(f"🔄 Round {round_number}/{definition.max_rounds}")

            round_start = datetime.now()

            # 主持人生成问题
            question = await moderator.generate_question(
                round_number=round_number,
                previous_round_summary=previous_summary
            )

            logger.info(f"Q{round_number}: {question[:80]}...")

            # 并发收集所有参与者的回答
            responses = await self._collect_responses(
                question=question,
                round_number=round_number,
                participant_agents=participant_agents,
                task_id=task_id
            )

            # 主持人总结本轮
            summary = await moderator.summarize_round(round_number, responses)
            previous_summary = summary

            # 创建轮次结果
            round_result = FocusGroupRoundResult(
                round_number=round_number,
                host_question=question,
                responses=responses,
                insights=[],  # 最终洞察在总结阶段提取
                started_at=round_start,
                completed_at=datetime.now()
            )

            # 添加到会话
            session.add_round(round_result)

            logger.info(
                f"Round {round_number} 完成: {len(responses)} 回答, "
                f"耗时: {round_result.duration_seconds:.2f}s"
            )

    async def _collect_responses(
        self,
        question: str,
        round_number: int,
        participant_agents: Dict[str, FocusGroupParticipantAgent],
        task_id: str
    ) -> List[FocusGroupMessage]:
        """
        并发收集参与者回答

        Args:
            question: 主持人的问题
            round_number: 轮次号
            participant_agents: 参与者Agent字典
            task_id: 任务ID

        Returns:
            List[FocusGroupMessage]: 所有参与者的回答
        """
        # 创建异步任务
        async_tasks = []

        for participant_id, agent in participant_agents.items():
            async def respond_task(agent=agent, pid=participant_id):
                response = await agent.respond_to_question(
                    question=question,
                    round_number=round_number,
                    participant_id=pid
                )
                # 更新任务进度
                await self.task_manager.update_progress(
                    task_id=task_id,
                    result={"participant_id": pid, "round": round_number},
                    success=not response.content.startswith("[Error:")
                )
                return response

            async_tasks.append(respond_task)

        # 使用带错误隔离的批量执行
        results = await self.concurrency_manager.execute_batch_with_isolation(
            tasks=async_tasks,
            max_concurrency=self.concurrency_manager.max_concurrency
        )

        # 收集成功的回答
        responses = []
        for result in results:
            if result["success"]:
                responses.append(result["data"])
            else:
                logger.warning(f"参与者回答失败: {result['error']}")

        return responses

    async def _extract_insights(
        self,
        session: FocusGroupSession,
        moderator: FocusGroupModeratorAgent
    ) -> List[Dict[str, Any]]:
        """
        总结阶段：从所有轮次中提取洞察

        Args:
            session: 会话对象
            moderator: 主持人Agent

        Returns:
            List[Dict]: 洞察列表
        """
        # 准备轮次数据
        all_rounds = []
        for round_result in session.rounds:
            round_data = {
                "round_number": round_result.round_number,
                "question": round_result.host_question,
                "response_count": round_result.response_count,
                "summary": None
            }

            # 如果回答数量较少，可以包含具体内容
            if round_result.response_count <= 10:
                round_data["responses"] = [r.content for r in round_result.responses]

            all_rounds.append(round_data)

        # 使用主持人提取洞察
        insights = await moderator.extract_insights(all_rounds)

        logger.info(f"提取到 {len(insights)} 条洞察")

        return insights

    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话状态

        Args:
            session_id: 会话ID

        Returns:
            会话状态信息
        """
        task = self.task_manager.get_active_task(f"focus_group_{session_id}")
        if task:
            return task.to_dict()
        return None


class SingleRoundFocusGroup:
    """
    单轮焦点小组工具类

    用于只需要一轮讨论的场景，简化接口
    """

    def __init__(
        self,
        max_concurrency: Optional[int] = None,
        model_id: str = "claude-3-5-sonnet-20241022"
    ):
        """
        初始化单轮焦点小组

        Args:
            max_concurrency: 最大并发数
            model_id: 使用的模型ID
        """
        self.concurrency_manager = ConcurrencyManager.for_focus_group()
        if max_concurrency:
            self.concurrency_manager.max_concurrency = max_concurrency
        self.model_id = model_id

    async def ask_question(
        self,
        question: str,
        audience_profiles: List[AudienceProfile],
        topic: str = "Focus Group Discussion",
        background: str = ""
    ) -> List[FocusGroupMessage]:
        """
        向一组受众提出单个问题

        Args:
            question: 要提出的问题
            audience_profiles: 受众画像列表
            topic: 讨论主题
            background: 背景信息

        Returns:
            List[FocusGroupMessage]: 所有参与者的回答
        """
        logger.info(
            f"单轮焦点小组: 向 {len(audience_profiles)} 人提问: {question[:50]}..."
        )

        # 创建临时焦点小组定义
        definition = FocusGroupDefinition(
            focus_group_id=str(uuid.uuid4()),
            title=topic,
            topic=topic,
            background=background,
            research_objectives=[],
            max_rounds=1
        )

        # 创建参与者Agent
        agents = []
        for profile in audience_profiles:
            agent = FocusGroupParticipantAgent(
                audience_profile=profile,
                focus_group=definition,
                model_id=self.model_id
            )
            agents.append((profile.user_id, agent))

        # 创建异步任务
        async_tasks = []
        for user_id, agent in agents:
            async def respond_task(agent=agent, uid=user_id):
                return await agent.respond_to_question(
                    question=question,
                    round_number=1,
                    participant_id=uid
                )
            async_tasks.append(respond_task)

        # 并发执行
        results = await self.concurrency_manager.execute_batch_with_isolation(
            tasks=async_tasks,
            max_concurrency=self.concurrency_manager.max_concurrency
        )

        # 收集结果
        responses = []
        for result in results:
            if result["success"]:
                responses.append(result["data"])

        logger.info(f"单轮焦点小组完成: 收到 {len(responses)}/{len(audience_profiles)} 回答")

        return responses
