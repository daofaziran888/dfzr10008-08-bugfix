<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">数据产品与API工厂</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向数据产品经理与开发者的数据产品快速构建平台。覆盖数据产品定义、API接口生成、数据模型封装、产品版本管理、调用配额控制、文档自动生成、产品市场分发与使用效果追踪的完整数据产品链路。</span>
        <span class="head-user">当前值班：{{ store.operator }} · {{ store.shiftLabel }}</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'

const store = useSessionStore()

const navItems = [{ label: "运营概览", path: "/" }, { label: "数据产品定义", path: "/product" }, { label: "API接口生成", path: "/apigen" }, { label: "数据模型封装", path: "/datapack" }, { label: "产品版本管理", path: "/version" }, { label: "调用配额控制", path: "/quota" }, { label: "文档自动生成", path: "/docgen" }, { label: "产品市场分发", path: "/market" }, { label: "使用效果追踪", path: "/usage" }, { label: "产品沙箱测试", path: "/sandbox" }, { label: "数据管线编排", path: "/pipeline" }, { label: "数据筛选引擎", path: "/filter" }, { label: "场景化配置模板", path: "/scene" }, { label: "实时数据推送", path: "/realtime" }, { label: "跨源数据关联", path: "/crossref" }, { label: "数据质量反馈", path: "/feedback" }, { label: "数据产品认证", path: "/badge" }]
</script>
