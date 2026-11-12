"""业务模块路由汇总。

这里统一按别名导入再暴露 ROUTERS：模块名有可能和内置名撞车（某个业务模块就叫 dict、list
这种名字时），按名字直接 import 会把内置类型覆盖掉，函数注解在运行时求值就会报
'module' object is not subscriptable。
"""
from __future__ import annotations

from app.routers import product as router_product
from app.routers import apigen as router_apigen
from app.routers import datapack as router_datapack
from app.routers import version as router_version
from app.routers import quota as router_quota
from app.routers import docgen as router_docgen
from app.routers import market as router_market
from app.routers import usage as router_usage
from app.routers import sandbox as router_sandbox
from app.routers import pipeline as router_pipeline
from app.routers import filter as router_filter
from app.routers import scene as router_scene
from app.routers import realtime as router_realtime
from app.routers import crossref as router_crossref
from app.routers import feedback as router_feedback
from app.routers import badge as router_badge

ROUTERS = [router_product, router_apigen, router_datapack, router_version, router_quota, router_docgen, router_market, router_usage, router_sandbox, router_pipeline, router_filter, router_scene, router_realtime, router_crossref, router_feedback, router_badge]
