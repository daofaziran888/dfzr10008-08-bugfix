<template>
  <section class="page" data-module="market">
    <header class="page-head">
      <div>
        <h2>产品市场分发管理</h2>
        <p class="page-desc">维护市场商品的定价方案、试用配置与描述信息，为产品市场分发提供可验证的数据工程流程。</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记市场商品</button>
        <button class="btn" type="button" @click="exportRows">导出产品市场分发清单</button>
      </div>
    </header>

    <!-- 市场分发实时跟随产品版本链路：只读未归档全量版本的兼容快照，不缓存旧灰度范围 -->
    <article class="distribution-card">
      <header class="dist-head">
        <strong>当前市场分发版本</strong>
        <span class="status-tag" :class="scope.distributing ? 'status-full' : 'status-archived'">
          {{ scope.distributing ? '分发中（全量 100%）' : '已停用' }}
        </span>
      </header>
      <p class="muted-text">{{ scope.message }}</p>
      <table v-if="scope.distributing" class="data-table">
        <tbody>
          <tr><th>版本编号</th><td>{{ scope.version?.['版本编号'] }}</td></tr>
          <tr><th>版本号</th><td>{{ scope.version?.['版本号'] }}</td></tr>
          <tr><th>兼容标识</th><td>{{ scope.compatibility_snapshot?.['兼容标识'] ?? '—' }}</td></tr>
          <tr><th>快照记录的原灰度范围</th><td>{{ scope.compatibility_snapshot?.['灰度范围'] ?? '—' }}</td></tr>
          <tr><th>实际分发比例</th><td>100%（全量发布，旧灰度范围不再生效）</td></tr>
        </tbody>
      </table>
    </article>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label class="filter-item">
        <span>商品编号</span>
        <input v-model="filters.keyword" placeholder="按商品编号检索" />
      </label>
      <label class="filter-item">
        <span>商品状态</span>
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
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in columns" :key="column">
            <span v-if="column === '商品状态'" class="status-tag" :class="statusClass(row.status)">{{ row.status }}</span>
            <template v-else>{{ row[column] ?? '—' }}</template>
          </td>
          <td class="row-actions">
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
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + 1" class="empty-state">暂无产品市场分发数据，可先登记市场商品</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条产品市场分发记录</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { request } from '@/api/client'

type Row = Record<string, string | number | null>
type DistributionScope = {
  distributing: boolean
  message: string
  version: Record<string, unknown> | null
  compatibility_snapshot: Record<string, unknown> | null
}

const ENDPOINT = '/api/market'
const columns = ['商品编号', '商品名称', '所属产品', '定价方案', '试用天数', '封面描述', '上线时间', '商品状态']
const statuses = ['草稿', '已上架', '已下架', '已删除']

const NEXT_ACTION: Record<string, string[]> = {
  草稿: ['上架商品'],
  已上架: ['下架商品'],
  已下架: ['删除商品'],
  已删除: [],
}

const rows = ref<Row[]>([])
const total = ref(0)
const errorMessage = ref('')
const filters = ref<{ keyword: string; status: string }>({ keyword: '', status: '' })
const scope = ref<DistributionScope>({
  distributing: false,
  message: '正在读取市场分发范围…',
  version: null,
  compatibility_snapshot: null,
})

const stats = ref([
  { label: '市场商品总数', value: 0 },
  { label: '已上架商品', value: 0 },
  { label: '已下架商品', value: 0 },
])

function availableActions(status: unknown): string[] {
  return NEXT_ACTION[String(status)] ?? []
}

function statusClass(status: unknown): string {
  return {
    草稿: 'status-draft',
    已上架: 'status-full',
    已下架: 'status-gray',
    已删除: 'status-archived',
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
  errorMessage.value = '市场商品登记入口尚未接入审批流'
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
      throw new Error(payload.message || '产品市场分发动作未生效，请稍后重试')
    }
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '产品市场分发操作失败'
  }
}

async function loadDistributionScope() {
  try {
    const response = await request(`${ENDPOINT}/distribution`)
    if (response.ok) {
      scope.value = (await response.json()) as DistributionScope
    }
  } catch {
    scope.value.message = '市场分发范围读取失败，请稍后重试'
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
      throw new Error('市场商品列表读取失败')
    }
    const payload = (await response.json()) as { items?: Row[]; total?: number }
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
    stats.value = [
      { label: '市场商品总数', value: rows.value.length },
      { label: '已上架商品', value: rows.value.filter((row) => row.status === '已上架').length },
      { label: '已下架商品', value: rows.value.filter((row) => row.status === '已下架').length },
    ]
    await loadDistributionScope()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '产品市场分发列表读取失败'
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
.distribution-card {
  background: #fff; border: 1px solid var(--border); border-radius: 8px;
  padding: 12px 16px; margin-bottom: 12px;
}
.dist-head { display: flex; justify-content: space-between; align-items: center; }
</style>
