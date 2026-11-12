import { createRouter, createWebHistory } from 'vue-router'

import Overview from '@/views/Overview.vue'
const Product = () => import('@/views/product/index.vue')
const Apigen = () => import('@/views/apigen/index.vue')
const Datapack = () => import('@/views/datapack/index.vue')
const Version = () => import('@/views/version/index.vue')
const Quota = () => import('@/views/quota/index.vue')
const Docgen = () => import('@/views/docgen/index.vue')
const Market = () => import('@/views/market/index.vue')
const Usage = () => import('@/views/usage/index.vue')
const Sandbox = () => import('@/views/sandbox/index.vue')
const Pipeline = () => import('@/views/pipeline/index.vue')
const Filter = () => import('@/views/filter/index.vue')
const Scene = () => import('@/views/scene/index.vue')
const Realtime = () => import('@/views/realtime/index.vue')
const Crossref = () => import('@/views/crossref/index.vue')
const Feedback = () => import('@/views/feedback/index.vue')
const Badge = () => import('@/views/badge/index.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'overview', component: Overview },
    { path: '/product', name: 'product', component: Product },
    { path: '/apigen', name: 'apigen', component: Apigen },
    { path: '/datapack', name: 'datapack', component: Datapack },
    { path: '/version', name: 'version', component: Version },
    { path: '/quota', name: 'quota', component: Quota },
    { path: '/docgen', name: 'docgen', component: Docgen },
    { path: '/market', name: 'market', component: Market },
    { path: '/usage', name: 'usage', component: Usage },
    { path: '/sandbox', name: 'sandbox', component: Sandbox },
    { path: '/pipeline', name: 'pipeline', component: Pipeline },
    { path: '/filter', name: 'filter', component: Filter },
    { path: '/scene', name: 'scene', component: Scene },
    { path: '/realtime', name: 'realtime', component: Realtime },
    { path: '/crossref', name: 'crossref', component: Crossref },
    { path: '/feedback', name: 'feedback', component: Feedback },
    { path: '/badge', name: 'badge', component: Badge },
  ],
})

export default router
