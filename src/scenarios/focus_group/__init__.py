"""
焦点小组场景模块
支持100-200并发的焦点小组批量执行

主要组件:
- BatchFocusGroupManager: 批量焦点小组管理器
- FocusGroupFactory: 焦点小组创建工厂

使用示例:
    from src.scenarios.focus_group import BatchFocusGroupManager, FocusGroupFactory

    # 创建焦点小组定义
    definitions = FocusGroupFactory.create_multiple_definitions(
        topic="产品反馈",
        audience_groups=[group1_profiles, group2_profiles],
        questions=["您对产品的第一印象是什么？", "有什么改进建议？"]
    )

    # 批量执行
    manager = BatchFocusGroupManager()
    result = await manager.run_batch(definitions)
"""

from src.scenarios.focus_group.batch_manager import (
    BatchFocusGroupManager,
    BatchFocusGroupResult,
    FocusGroupFactory
)

__all__ = [
    "BatchFocusGroupManager",
    "BatchFocusGroupResult",
    "FocusGroupFactory"
]
