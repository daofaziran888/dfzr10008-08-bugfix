"""接口出入参模型：列表分页、动作结果与各模块的明细结构。"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    size: int = 20


class ActionResult(BaseModel):
    ok: bool
    message: str
    entry: dict[str, Any] | None = None


class EntryPayload(BaseModel):
    """登记或修改一条业务记录时提交的字段集合。"""

    values: dict[str, Any] = Field(default_factory=dict)
    remark: str | None = None



class ProductEntry(BaseModel):
    """数据产品明细结构。"""

    field_0: str | None = None  # 产品编号
    field_1: str | None = None  # 产品名称
    field_2: str | None = None  # 产品类型
    field_3: str | None = None  # 数据来源
    field_4: str | None = None  # 计算逻辑
    field_5: str | None = None  # 输出格式
    field_6: str | None = None  # 负责人
    field_7: str | None = None  # 产品状态

class ApigenEntry(BaseModel):
    """接口配置明细结构。"""

    field_0: str | None = None  # 接口编号
    field_1: str | None = None  # 接口名称
    field_2: str | None = None  # 请求方法
    field_3: str | None = None  # 请求路径
    field_4: str | None = None  # 参数定义
    field_5: str | None = None  # 响应模板
    field_6: str | None = None  # 超时秒数
    field_7: str | None = None  # 接口状态

class DatapackEntry(BaseModel):
    """模型封装明细结构。"""

    field_0: str | None = None  # 封装编号
    field_1: str | None = None  # 封装名称
    field_2: str | None = None  # 原始数据源
    field_3: str | None = None  # 输出结构
    field_4: str | None = None  # 字段映射
    field_5: str | None = None  # 聚合规则
    field_6: str | None = None  # 缓存策略
    field_7: str | None = None  # 封装状态

class VersionEntry(BaseModel):
    """产品版本明细结构。"""

    field_0: str | None = None  # 版本编号
    field_1: str | None = None  # 产品名称
    field_2: str | None = None  # 版本号
    field_3: str | None = None  # 变更日志
    field_4: str | None = None  # 兼容标识
    field_5: str | None = None  # 灰度比例
    field_6: str | None = None  # 全量时间
    field_7: str | None = None  # 版本状态

class QuotaEntry(BaseModel):
    """配额配置明细结构。"""

    field_0: str | None = None  # 配置编号
    field_1: str | None = None  # 调用方名称
    field_2: str | None = None  # 每秒上限
    field_3: str | None = None  # 日调用上限
    field_4: str | None = None  # 并发限制
    field_5: str | None = None  # 超限策略
    field_6: str | None = None  # 有效期至
    field_7: str | None = None  # 配额状态

class DocgenEntry(BaseModel):
    """文档模板明细结构。"""

    field_0: str | None = None  # 模板编号
    field_1: str | None = None  # 文档标题
    field_2: str | None = None  # 目标接口
    field_3: str | None = None  # 生成格式
    field_4: str | None = None  # 示例数据
    field_5: str | None = None  # 错误码表
    field_6: str | None = None  # 更新触发
    field_7: str | None = None  # 模板状态

class MarketEntry(BaseModel):
    """市场商品明细结构。"""

    field_0: str | None = None  # 商品编号
    field_1: str | None = None  # 商品名称
    field_2: str | None = None  # 所属产品
    field_3: str | None = None  # 定价方案
    field_4: str | None = None  # 试用天数
    field_5: str | None = None  # 封面描述
    field_6: str | None = None  # 上线时间
    field_7: str | None = None  # 商品状态

class UsageEntry(BaseModel):
    """使用记录明细结构。"""

    field_0: str | None = None  # 记录编号
    field_1: str | None = None  # 产品名称
    field_2: str | None = None  # 调用方名称
    field_3: str | None = None  # 调用次数
    field_4: str | None = None  # 平均耗时
    field_5: str | None = None  # 错误次数
    field_6: str | None = None  # 统计周期
    field_7: str | None = None  # 记录状态

class SandboxEntry(BaseModel):
    """沙箱实例明细结构。"""

    field_0: str | None = None  # 实例编号
    field_1: str | None = None  # 测试产品
    field_2: str | None = None  # 测试参数
    field_3: str | None = None  # 预期输出
    field_4: str | None = None  # 实际输出
    field_5: str | None = None  # 差异对比
    field_6: str | None = None  # 测试耗时
    field_7: str | None = None  # 实例状态

class PipelineEntry(BaseModel):
    """管线节点明细结构。"""

    field_0: str | None = None  # 节点编号
    field_1: str | None = None  # 节点名称
    field_2: str | None = None  # 上游节点
    field_3: str | None = None  # 处理逻辑
    field_4: str | None = None  # 输出格式
    field_5: str | None = None  # 错误处理
    field_6: str | None = None  # 重试策略
    field_7: str | None = None  # 节点状态

class FilterEntry(BaseModel):
    """筛选模板明细结构。"""

    field_0: str | None = None  # 模板编号
    field_1: str | None = None  # 模板名称
    field_2: str | None = None  # 目标数据源
    field_3: str | None = None  # 筛选条件
    field_4: str | None = None  # 排序字段
    field_5: str | None = None  # 分页配置
    field_6: str | None = None  # 结果格式
    field_7: str | None = None  # 模板状态

class SceneEntry(BaseModel):
    """场景模板明细结构。"""

    field_0: str | None = None  # 模板编号
    field_1: str | None = None  # 模板名称
    field_2: str | None = None  # 适用场景
    field_3: str | None = None  # 预设指标
    field_4: str | None = None  # 推荐图表
    field_5: str | None = None  # 默认参数
    field_6: str | None = None  # 模板描述
    field_7: str | None = None  # 模板状态

class RealtimeEntry(BaseModel):
    """推送通道明细结构。"""

    field_0: str | None = None  # 通道编号
    field_1: str | None = None  # 通道名称
    field_2: str | None = None  # 数据源名称
    field_3: str | None = None  # 推送协议
    field_4: str | None = None  # 压缩格式
    field_5: str | None = None  # 心跳间隔
    field_6: str | None = None  # 断线重连
    field_7: str | None = None  # 通道状态

class CrossrefEntry(BaseModel):
    """关联规则明细结构。"""

    field_0: str | None = None  # 规则编号
    field_1: str | None = None  # 主数据源
    field_2: str | None = None  # 关联数据源
    field_3: str | None = None  # 关联字段
    field_4: str | None = None  # 关联类型
    field_5: str | None = None  # 结果字段
    field_6: str | None = None  # 时效控制
    field_7: str | None = None  # 规则状态

class FeedbackEntry(BaseModel):
    """反馈记录明细结构。"""

    field_0: str | None = None  # 反馈编号
    field_1: str | None = None  # 数据产品
    field_2: str | None = None  # 反馈类型
    field_3: str | None = None  # 反馈内容
    field_4: str | None = None  # 严重程度
    field_5: str | None = None  # 处理状态
    field_6: str | None = None  # 反馈人
    field_7: str | None = None  # 反馈时间

class BadgeEntry(BaseModel):
    """认证记录明细结构。"""

    field_0: str | None = None  # 认证编号
    field_1: str | None = None  # 产品名称
    field_2: str | None = None  # 认证类型
    field_3: str | None = None  # 认证标准
    field_4: str | None = None  # 认证机构
    field_5: str | None = None  # 有效期限
    field_6: str | None = None  # 认证结果
    field_7: str | None = None  # 认证状态
