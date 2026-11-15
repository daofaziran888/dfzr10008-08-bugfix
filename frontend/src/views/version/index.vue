<template>
  <section class="page" data-module="version">
    <header class="page-head">
      <div>
        <h2>产品版本管理管理</h2>
        <p class="page-desc">维护产品版本的变更日志、兼容标识与灰度策略，为产品版本管理提供可验证的数据工程流程。</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记产品版本</button>
        <button class="btn" type="button" @click="exportRows">导出产品版本管理清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label class="filter-item">
        <span>版本编号</span>
        <input v-model="filters.keyword" placeholder="按版本编号检索" />
      </label>
      <label class="filter-item">
        <span>版本状态</span>
        <select v-model="filters.status">
          <option value="">全部状态</option>
          <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
        </select>
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
          <th>可执行动作</th>
          <th>详情</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in columns" :key="column">
            <span v-if="column === '版本状态'" class="status-tag" :class="statusClass(row.status)">{{ row.status }}</span>
            <template v-else>{{ row[column] ?? '—' }}</template>
          </td>
          <td class="row-actions">
            <!-- 动作入口严格跟随当前状态，旧版本不再重复显示不可执行的动作 -->
            <button
              v-for="action in availableActions(row.status)"
              :key="action"
              class="link"
              type="button"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
            <span v-if="!availableActions(row.status).length" class="muted-text">—</span>
          </td>
          <td>
            <button class="link" type="button" @click="openDetail(row)">查看兼容快照</button>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + 2" class="empty-state">暂无产品版本管理数据，可先登记产品版本</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条产品版本管理记录</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>

    <div v-if="detail" class="modal-mask" @click.self="detail = null">
      <div class="modal-card">
        <header class="modal-head">
          <strong>{{ detail['版本编号'] }} 兼容快照</strong>
          <button class="btn ghost" type="button" @click="detail = null">关闭</button>
        </header>
        <table class="data-table">
          <tbody>
            <tr><th>当前状态</th><td><span class="status-tag" :class="statusClass(detail.status)">{{ detail.status }}</span></td></tr>
            <tr><th>版本号</th><td>{{ detail['版本号'] ?? '—' }}</td></tr>
            <tr><th>兼容标识（实时字段）</th><td>{{ detail['兼容标识'] ?? '—' }}</td></tr>
            <tr><th>灰度比例</th><td>{{ detail['灰度比例'] ?? '—' }}</td></tr>
            <tr><th>全量时间</th><td>{{ detail['全量时间'] ?? '—' }}</td></tr>
          </tbody>
        </table>
        <h4 class="snapshot-title">全量发布时固化的兼容快照（归档后不可改写）</h4>
        <table v-if="detail['兼容快照']" class="data-table">
          <tbody>
            <tr v-for="(value, key) in detail['兼容快照']" :key="key">
              <th>{{ key }}</th>
              <td>{{ value ?? '—' }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="muted-text">该版本尚未全量发布，暂无兼容快照；全量发布时才会固化。</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { request } from '@/api/client'

type Row = Record<string, string | number | null | Record<string, unknown>>
type Snapshot = Record<string, unknown>

const ENDPOINT = '/api/version'
const columns = ['版本编号', '产品名称', '版本号', '变更日志', '兼容标识', '灰度比例', '全量时间', '版本状态']
const statuses = ['草稿', '灰度中', '全量发布', '已归档']

// 状态机：只暴露当前状态唯一合法的下一步动作，避免旧动作残留造成回退或跳级。
const NEXT_ACTION: Record<string, string[]> = {
  草稿: ['灰度发布'],
  灰度中: ['全量发布'],
  全量发布: ['归档版本'],
  已归档: ['恢复版本'],
}

const rows = ref<Row[]>([])
const total = ref(0)
const errorMessage = ref('')
const detail = ref<Row | null>(null)
const filters = ref<{ keyword: string; status: string }>({ keyword: '', status: '' })

const stats = computed(() => [
  { label: '产品版本总数', value: rows.value.length },
  { label: '灰度中版本', value: rows.value.filter((row) => row.status === '灰度中').length },
  { label: '全量发布版本', value: rows.value.filter((row) => row.status === '全量发布').length },
])

function availableActions(status: unknown): string[] {
  return NEXT_ACTION[String(status)] ?? []
}

function statusClass(status: unknown): string {
  return {
    草稿: 'status-draft',
    灰度中: 'status-gray',
    全量发布: 'status-full',
    已归档: 'status-archived',
  }[String(status)] ?? ''
}

function resetFilters() {
  filters.value = { keyword: '', status: '' }
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  errorMessage.value = '产品版本登记入口尚未接入审批流'
}

function openDetail(row: Row) {
  detail.value = row
}

async function runAction(action: string, row: Row) {
  errorMessage.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    })
    const payload = (await response.json()) as { ok: boolean; message: string }
    if (!response.ok || !payload.ok) {
      // 被规则拦下（并发全量互斥、状态不符等）时原样展示后端原因，不改本地列表。
      throw new Error(payload.message || '产品版本管理动作未生效，请稍后重试')
    }
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '产品版本管理操作失败'
  }
}

async function reload() {
  errorMessage.value = ''
  const query = new URLSearchParams()
  if (filters.value.keyword) query.set('keyword', filters.value.keyword)
  if (filters.value.status) query.set('status', filters.value.status)
  try {
    const response = await request(`${ENDPOINT}?${query.toString()}`)
    if (!response.ok) {
      throw new Error('产品版本列表读取失败')
    }
    const payload = (await response.json()) as { items?: Row[]; total?: number }
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
    // 详情弹窗若开着，同步刷新成最新快照，避免展示错位的旧数据。
    if (detail.value) {
      const latest = rows.value.find((row) => String(row.id) === String(detail.value?.id))
      detail.value = latest ?? detail.value
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '产品版本管理列表读取失败'
  }
}

onMounted(reload)
</script>

<style scoped>
.muted-text { color: var(--muted); font-size: 12px; }
.status-tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
.status-draft { background: #e2e8f0; color: #475569; }
.status-gray { background: #fef3c7; color: #b45309; }
.status-full { background: #dcfce7; color: #15803d; }
.status-archived { background: #e5e7eb; color: #6b7280; }
.modal-mask {
  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.45);
  display: flex; align-items: center; justify-content: center; z-index: 20;
}
.modal-card { background: #fff; border-radius: 10px; width: 560px; max-width: 92vw; padding: 18px 20px; }
.modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.snapshot-title { margin: 16px 0 8px; font-size: 14px; }
</style>
