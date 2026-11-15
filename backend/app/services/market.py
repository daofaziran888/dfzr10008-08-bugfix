"""产品市场分发业务规则：状态流转、字段校验与筛选口径都收在这里。

市场分发使用的版本范围不允许自己缓存：每次都沿产品版本链路实时读取唯一处于
「全量发布」且未归档的版本及其兼容快照。版本归档后立即从分发范围摘除，
旧灰度范围随之失效，避免继续按灰度比例对外分发。
"""
from __future__ import annotations

from typing import Any

from app.store import store
from app.services.version import VersionService

MODULE = "market"
REQUIRED_FIELDS = ["商品编号", "商品名称", "所属产品"]
STATUS_ORDER = ["草稿", "已上架", "已下架", "已删除"]
ACTION_RULES = {"上架商品": "草稿", "下架商品": "已上架", "删除商品": "已下架"}
NEGATIVE_ACTIONS = []

version_service = VersionService()


class MarketService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = store.rows(MODULE)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("商品编号", ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        return store.find(MODULE, entry_id)

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
        missing = [field for field in REQUIRED_FIELDS if not str(values.get(field) or "").strip()]
        if missing:
            return None, missing
        rows = store.rows(MODULE)
        entry = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        entry.update({field: values.get(field) for field in REQUIRED_FIELDS})
        entry["status"] = STATUS_ORDER[0]
        entry["商品状态"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        rows.append(entry)
        return entry, []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"市场商品 {entry_id} 不存在或已归档"
        if action not in ACTION_RULES:
            return None, f"动作「{action}」不属于产品市场分发可执行范围"
        target = ACTION_RULES[action]
        if target not in STATUS_ORDER:
            return None, f"目标状态「{target}」不在允许的状态序列里"
        entry["status"] = target
        entry["商品状态"] = target
        entry["pending"] = target != STATUS_ORDER[-1]
        entry["abnormal"] = action in NEGATIVE_ACTIONS
        return entry, f"市场商品已{action}"

    def distribution_scope(self) -> dict[str, Any]:
        """市场分发当前应使用的版本与兼容快照。

        只认未归档的全量发布版本：该版本归档后这里立即返回停用，任何历史灰度范围
        都不会再被市场分发读取。
        """
        active = version_service.active_full_release()
        if active is None:
            return {
                "distributing": False,
                "message": "当前没有处于全量发布且未归档的版本，市场分发已停用旧灰度范围",
                "version": None,
                "compatibility_snapshot": None,
            }
        snapshot = active.get("兼容快照") or {
            "兼容标识": active.get("兼容标识"),
            "版本号": active.get("版本号"),
            "灰度范围": active.get("灰度比例"),
            "全量时间": active.get("全量时间"),
        }
        return {
            "distributing": True,
            "message": "市场分发跟随唯一全量发布版本，按全量范围（100%）分发",
            "version": {
                "id": active.get("id"),
                "版本编号": active.get("版本编号"),
                "版本号": active.get("版本号"),
                "status": active.get("status"),
                "灰度比例": "100%",
            },
            "compatibility_snapshot": snapshot,
        }
