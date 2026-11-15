"""端到端校验：版本动作 -> 兼容快照 -> 市场读取 整条链路（走真实 HTTP 服务）。"""
import json
import threading
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    print(("PASS" if condition else "FAIL"), "-", name, detail)
    if not condition:
        failures.append(name)


def request(method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())


def get(version_id: int) -> dict:
    return request("GET", f"/api/version/{version_id}")[1]


def act(version_id: int, action: str) -> dict:
    return request("POST", f"/api/version/{version_id}/actions", {"action": action})[1]


# ---------- 初始种子 ----------
v2 = get(2)
v3 = get(3)
v4 = get(4)
check("VERS-0002 初始灰度中且 20%", v2["status"] == "灰度中" and v2["灰度比例"] == "20%")
check("VERS-0003 初始全量发布且兼容标识 v1", v3["status"] == "全量发布" and v3["兼容标识"] == "v1")
check("VERS-0003 已带固化兼容快照", v3["兼容快照"]["兼容标识"] == "v1")
check("VERS-0004 初始灰度中且 10%", v4["status"] == "灰度中" and v4["灰度比例"] == "10%")

# ---------- 市场初始跟随 VERS-0003 ----------
dist = request("GET", "/api/market/distribution")[1]
check("市场初始读取 VERS-0003 全量", dist["distributing"] and dist["version"]["版本编号"] == "VERS-0003")
check("市场使用快照兼容标识 v1", dist["compatibility_snapshot"]["兼容标识"] == "v1")
check("市场按全量 100% 而非旧灰度", dist["version"]["灰度比例"] == "100%")

# ---------- 互斥：全量存在时 VERS-0002 全量发布被拦下 ----------
result = act(2, "全量发布")
check("互斥：VERS-0002 全量被拒", result["ok"] is False)
v2_after = get(2)
check("互斥：VERS-0002 保持灰度中与 20%", v2_after["status"] == "灰度中" and v2_after["灰度比例"] == "20%")

# ---------- 非法流转：回退与跳级必须拒绝 ----------
result = act(2, "灰度发布")
check("禁止回退：灰度中再灰度发布被拒", result["ok"] is False and get(2)["status"] == "灰度中")
result = act(2, "归档版本")
check("禁止跳级：灰度中直接归档被拒", result["ok"] is False and get(2)["status"] == "灰度中")

# ---------- 归档 VERS-0003：市场停止使用，快照保留 ----------
snapshot_before = json.loads(json.dumps(v3["兼容快照"]))
result = act(3, "归档版本")
check("VERS-0003 归档成功", result["ok"] and result["entry"]["status"] == "已归档")
v3_archived = get(3)
check("归档后兼容快照原样保留", v3_archived["兼容快照"] == snapshot_before)
check("归档后兼容标识仍为 v1", v3_archived["兼容标识"] == "v1")
dist = request("GET", "/api/market/distribution")[1]
check("归档后市场停用且不读旧版本/灰度", not dist["distributing"] and dist["version"] is None)

# ---------- VERS-0002 全量发布：进入全量并保留原兼容标识 ----------
result = act(2, "全量发布")
check("VERS-0002 全量发布成功", result["ok"] and result["entry"]["status"] == "全量发布")
v2_full = get(2)
check("VERS-0002 保留原兼容标识 v1", v2_full["兼容标识"] == "v1")
check("VERS-0002 全量时生成兼容快照", v2_full["兼容快照"]["兼容标识"] == "v1")
check("快照记录原灰度范围 20%", v2_full["兼容快照"]["灰度范围"] == "20%")
check("VERS-0002 全量后灰度比例 100%", v2_full["灰度比例"] == "100%")

# ---------- 市场改跟 VERS-0002 ----------
dist = request("GET", "/api/market/distribution")[1]
check("市场改跟 VERS-0002", dist["distributing"] and dist["version"]["版本编号"] == "VERS-0002")

# ---------- 并发：两个运营同时对 VERS-0002 与 VERS-0004 发起全量发布 ----------
# 先归档 VERS-0002 腾出全量位置，再并发让 0002(恢复版本) 与 0004(全量发布) 竞争全量。
act(2, "归档版本")
outcomes: list[tuple[int, dict]] = []
barrier = threading.Barrier(2)


def worker(version_id: int, action: str) -> None:
    barrier.wait()  # 尽量让两个请求同时打到服务
    outcomes.append((version_id, act(version_id, action)))


t1 = threading.Thread(target=worker, args=(2, "恢复版本"))
t2 = threading.Thread(target=worker, args=(4, "全量发布"))
t1.start()
t2.start()
t1.join()
t2.join()

ok_versions = [vid for vid, res in outcomes if res.get("ok")]
check("并发后恰好一个版本进入全量", len(ok_versions) == 1, str(ok_versions))
winner = ok_versions[0]
loser = next(vid for vid, _ in outcomes if vid not in ok_versions)
loser_row = get(loser)
check("落选版本保持原状态", loser_row["status"] == ("已归档" if loser == 2 else "灰度中"))
check("落选版本保持原灰度范围", loser_row["灰度比例"] == ("100%" if loser == 2 else "10%"))
check("胜出版本处于全量发布", get(winner)["status"] == "全量发布")
dist = request("GET", "/api/market/distribution")[1]
check("市场只跟随胜出的全量版本", dist["version"]["id"] == winner)

# ---------- 恢复只回到上一合法状态且不改写快照 ----------
act(winner, "归档版本")
if loser == 2:
    result = act(2, "恢复版本")
    check("归档后恢复回到全量发布", result["ok"] and get(2)["status"] == "全量发布")
    check("恢复不重写快照", get(2)["兼容快照"]["灰度范围"] == "20%")

# ---------- 草稿版本只能先灰度发布 ----------
result = act(1, "全量发布")
check("草稿禁止跳级全量", result["ok"] is False and get(1)["status"] == "草稿")
result = act(1, "灰度发布")
check("草稿可灰度发布", result["ok"] and get(1)["status"] == "灰度中")

# ---------- 未知动作与不存在记录 ----------
check("未知动作被拒", act(1, "删除版本")["ok"] is False)
check("不存在记录报错", request("POST", "/api/version/999/actions", {"action": "全量发布"})[1]["ok"] is False)

# ---------- values.action 提交方式同样兼容（当前存在全量版本，应被互斥规则拦下） ----------
status_code, body = request("POST", "/api/version/1/actions", {"values": {"action": "全量发布"}})
check("values.action 提交兼容", body["ok"] is False and "只允许一个版本全量" in body["message"])

# ---------- /export 路由不再被 /{entry_id} 吞掉 ----------
code1, body1 = request("GET", "/api/version/export")
check("/api/version/export 正常导出", code1 == 200 and body1["module"] == "version")
code2, body2 = request("GET", "/api/market/export")
check("/api/market/export 正常导出", code2 == 200 and body2["module"] == "market")

# ---------- 列表过滤 ----------
code, body = request("GET", "/api/version?status=%E5%B7%B2%E5%BD%92%E6%A1%A3")
check("按状态过滤列表", code == 200 and all(row["status"] == "已归档" for row in body["items"]))

print()
if failures:
    print(f"{len(failures)} 项失败：{failures}")
    raise SystemExit(1)
print("全部校验通过")
