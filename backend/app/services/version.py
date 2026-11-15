"""产品版本管理业务规则：状态流转、字段校验与筛选口径都收在这里。

状态机（只允许逐级推进，禁止切换或跳级）：
    草稿 --灰度发布--> 灰度中 --全量发布--> 全量发布 --归档版本--> 已归档
    已归档 --恢复版本--> 全量发布（只回到上一合法状态）

附加规则：
- 全量发布是互斥动作：同一时刻只允许一个版本处于「全量发布」，并发请求由锁串行化，
  落选版本保持原状态与原灰度范围，不做任何改写。
- 进入「全量发布」时固化一份兼容快照（兼容标识、灰度范围等）；归档后该快照不可改写，
  市场分发只能读取未归档全量版本的快照，不能再沿用历史灰度范围。
"""
from __future__ import annotations

import threading
from datetime import date
from typing import Any

from app.store import store

MODULE = "version"
REQUIRED_FIELDS = ["版本编号", "产品名称", "版本号"]
DRAFT, GRAY, FULL, ARCHIVED = ("草稿", "灰度中", "全量发布", "已归档")
STATUS_ORDER = [DRAFT, GRAY, FULL, ARCHIVED]

# 动作 -> (允许执行的当前状态, 动作完成后的目标状态)
ACTION_RULES: dict[str, tuple[str, str]] = {
    "灰度发布": (DRAFT, GRAY),
    "全量发布": (GRAY, FULL),
    "归档版本": (FULL, ARCHIVED),
    "恢复版本": (ARCHIVED, FULL),
}
# 这两个动作执行后系统中会出现（或恢复出）一个全量发布版本，必须走互斥校验。
FULL_RELEASE_GUARDED_ACTIONS = ("全量发布", "恢复版本")
SNAPSHOT_FIELDS = ("兼容标识", "版本号", "变更日志")

# 全量发布互斥锁：内存存储下保证并发全量发布只有一个版本能落库。
_full_release_lock = threading.Lock()


class VersionService:
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
            rows = [row for row in rows if keyword in str(row.get("版本编号", ""))]
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
        entry["版本状态"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        rows.append(entry)
        return entry, []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"产品版本 {entry_id} 不存在或已归档"
        rule = ACTION_RULES.get(action)
        if rule is None:
            return None, f"动作「{action}」不属于产品版本管理可执行范围"
        required_status, target_status = rule
        current_status = str(entry.get("status") or "")
        # 严格逐级流转：当前状态必须正好是该动作要求的前置状态，禁止回退与跳级。
        if current_status != required_status:
            return None, (
                f"当前状态为「{current_status}」，仅「{required_status}」状态可执行{action}；"
                "产品版本只能按草稿、灰度中、全量发布、已归档逐级流转"
            )

        if action in FULL_RELEASE_GUARDED_ACTIONS:
            # 锁内重新检查：并发全量发布时只有一个版本能通过，其余原样保留。
            with _full_release_lock:
                active = self._find_full_release(exclude_id=entry_id)
                if active is not None:
                    return None, (
                        f"版本 {active.get('版本编号')} 已处于全量发布，同一时间只允许一个版本全量；"
                        "本次操作未生效，原状态与灰度范围保持不变"
                    )
                self._apply_transition(entry, action, target_status)
        else:
            self._apply_transition(entry, action, target_status)
        return entry, f"产品版本已{action}"

    def _apply_transition(self, entry: dict[str, Any], action: str, target_status: str) -> None:
        if action == "全量发布":
            # 进入全量时固化兼容快照，并把分发范围从灰度比例扩到全量。
            entry["兼容快照"] = self._build_snapshot(entry)
            entry["全量时间"] = date.today().isoformat()
            entry["灰度比例"] = "100%"
        # 归档、恢复都不会重写兼容快照：归档后快照只读，恢复沿用归档前的快照。
        entry["status"] = target_status
        entry["版本状态"] = target_status
        entry["pending"] = target_status != ARCHIVED
        entry["abnormal"] = False

    def _build_snapshot(self, entry: dict[str, Any]) -> dict[str, Any]:
        snapshot = {field: entry.get(field) for field in SNAPSHOT_FIELDS}
        # 记录进入全量前的原始灰度范围，便于审计；市场分发本身按全量读取。
        snapshot["灰度范围"] = entry.get("灰度比例")
        snapshot["全量时间"] = entry.get("全量时间") or date.today().isoformat()
        return snapshot

    def _find_full_release(self, *, exclude_id: int | None = None) -> dict[str, Any] | None:
        for row in store.rows(MODULE):
            if row.get("status") == FULL and int(row.get("id", 0)) != exclude_id:
                return row
        return None

    def active_full_release(self) -> dict[str, Any] | None:
        """市场分发唯一可读的版本：未归档的全量发布版本；归档版本不会出现在这里。"""
        return self._find_full_release()
