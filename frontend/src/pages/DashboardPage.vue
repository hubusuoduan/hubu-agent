<template>
  <div class="dashboard-page">
    <div class="dashboard-page-inner">
      <!-- 顶部 Banner -->
      <div class="dashboard-banner">
        <div class="banner-content">
          <div class="banner-info">
            <div class="banner-icon">
              <span style="font-size: 28px">📊</span>
            </div>
            <div class="banner-text">
              <h2>Token 用量统计</h2>
              <p>查看 Token 消耗趋势与调用统计</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 筛选器 -->
      <div class="filter-bar">
        <div class="filter-left">
          <el-select v-model="selectedModel" placeholder="全部模型" clearable style="width: 200px" @change="loadData">
            <el-option label="全部模型" value="" />
            <el-option v-for="m in modelList" :key="m" :label="m" :value="m" />
          </el-select>
          <el-radio-group v-model="timeRange" @change="loadData">
            <el-radio-button :value="7">近7天</el-radio-button>
            <el-radio-button :value="30">近30天</el-radio-button>
            <el-radio-button :value="90">近90天</el-radio-button>
            <el-radio-button :value="365">全部</el-radio-button>
          </el-radio-group>
        </div>
        <el-button @click="loadData" :loading="loading" type="primary" plain round>
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <!-- KPI 卡片 -->
      <div class="kpi-cards">
        <div class="kpi-card kpi-calls">
          <div class="kpi-icon">📞</div>
          <div class="kpi-info">
            <div class="kpi-value">{{ totalCount.toLocaleString() }}</div>
            <div class="kpi-label">总调用次数</div>
          </div>
        </div>
        <div class="kpi-card kpi-input">
          <div class="kpi-icon">📥</div>
          <div class="kpi-info">
            <div class="kpi-value">{{ formatTokens(totalInputTokens) }}</div>
            <div class="kpi-label">输入 Token</div>
          </div>
        </div>
        <div class="kpi-card kpi-output">
          <div class="kpi-icon">📤</div>
          <div class="kpi-info">
            <div class="kpi-value">{{ formatTokens(totalOutputTokens) }}</div>
            <div class="kpi-label">输出 Token</div>
          </div>
        </div>
        <div class="kpi-card kpi-total">
          <div class="kpi-icon">💰</div>
          <div class="kpi-info">
            <div class="kpi-value">{{ formatTokens(totalTokens) }}</div>
            <div class="kpi-label">总 Token</div>
          </div>
        </div>
      </div>

      <!-- 图表区域 -->
      <div v-loading="loading" class="charts-area">
        <div class="chart-card">
          <div class="chart-title">调用次数趋势</div>
          <div ref="countChartRef" class="chart-container"></div>
        </div>
        <div class="chart-card">
          <div class="chart-title">Token 使用量</div>
          <div ref="tokenChartRef" class="chart-container"></div>
        </div>
      </div>

      <!-- 暂无数据 -->
      <el-empty v-if="!loading && totalCount === 0" description="暂无 Token 使用数据，开始对话后将自动统计" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getUsageStats, getUsageCount, getModelsList } from '../apis/usage-stats'
import type { UsageRecord, UsageCountRecord } from '../apis/usage-stats'

// 筛选状态
const selectedModel = ref('')
const timeRange = ref(7)
const modelList = ref<string[]>([])
const loading = ref(false)

// 数据
const usageData = ref<UsageRecord[]>([])
const countData = ref<UsageCountRecord[]>([])

// KPI 汇总
const totalCount = computed(() => countData.value.reduce((sum, r) => sum + r.count, 0))
const totalInputTokens = computed(() => usageData.value.reduce((sum, r) => sum + r.input_tokens, 0))
const totalOutputTokens = computed(() => usageData.value.reduce((sum, r) => sum + r.output_tokens, 0))
const totalTokens = computed(() => usageData.value.reduce((sum, r) => sum + r.total_tokens, 0))

// 图表 DOM 引用
const countChartRef = ref<HTMLElement>()
const tokenChartRef = ref<HTMLElement>()
let countChart: echarts.ECharts | null = null
let tokenChart: echarts.ECharts | null = null

// 格式化 Token 数量
function formatTokens(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return n.toLocaleString()
}

// 加载模型列表
async function loadModels() {
  try {
    const res = await getModelsList()
    modelList.value = res.models || []
  } catch {
    modelList.value = []
  }
}

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const query = {
      delta_days: timeRange.value,
      model: selectedModel.value || undefined,
    }
    const [usageRes, countRes] = await Promise.all([
      getUsageStats(query),
      getUsageCount(query),
    ])
    usageData.value = usageRes.data || []
    countData.value = countRes.data || []

    await nextTick()
    renderCharts()
  } catch (e: any) {
    console.error('加载统计数据失败:', e)
  } finally {
    loading.value = false
  }
}

// 获取日期列表（填充空缺日期）
function getDateRange(data: { date: string }[]): string[] {
  if (data.length === 0) return []
  const dates = data.map(r => r.date).sort()
  const start = new Date(dates[0])
  const end = new Date(dates[dates.length - 1])
  const result: string[] = []
  const d = new Date(start)
  while (d <= end) {
    result.push(d.toISOString().slice(0, 10))
    d.setDate(d.getDate() + 1)
  }
  return result
}

// 获取所有模型
function getModels(data: { model: string }[]): string[] {
  return [...new Set(data.map(r => r.model))].sort()
}

// 渲染图表
function renderCharts() {
  renderCountChart()
  renderTokenChart()
}

// 渲染调用次数折线图
function renderCountChart() {
  if (!countChartRef.value) return
  if (!countChart) {
    countChart = echarts.init(countChartRef.value)
  }

  const dates = getDateRange(countData.value)
  const models = getModels(countData.value)

  // 每个模型一条折线
  const series = models.map(model => {
    const modelData = countData.value.filter(r => r.model === model)
    const map = new Map(modelData.map(r => [r.date, r.count]))
    return {
      name: model,
      type: 'line' as const,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: dates.map(d => map.get(d) ?? 0),
    }
  })

  countChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    legend: {
      data: models,
      bottom: 0,
      textStyle: { fontSize: 12 },
    },
    grid: {
      left: 60,
      right: 20,
      top: 20,
      bottom: 40,
    },
    xAxis: {
      type: 'category',
      data: dates.map(d => d.slice(5)),  // 只显示 MM-DD
      axisLabel: { fontSize: 11, color: '#9ca3af' },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 11, color: '#9ca3af' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series,
    color: ['#6366f1', '#06b6d4', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'],
  })
}

// 渲染 Token 使用量堆叠柱状图
function renderTokenChart() {
  if (!tokenChartRef.value) return
  if (!tokenChart) {
    tokenChart = echarts.init(tokenChartRef.value)
  }

  const dates = getDateRange(usageData.value)

  // 按日期聚合 input/output（不区分模型，简化展示）
  const inputByDate = new Map<string, number>()
  const outputByDate = new Map<string, number>()
  for (const r of usageData.value) {
    inputByDate.set(r.date, (inputByDate.get(r.date) ?? 0) + r.input_tokens)
    outputByDate.set(r.date, (outputByDate.get(r.date) ?? 0) + r.output_tokens)
  }

  const inputData = dates.map(d => inputByDate.get(d) ?? 0)
  const outputData = dates.map(d => outputByDate.get(d) ?? 0)
  const totalData = dates.map((d, i) => inputData[i] + outputData[i])

  tokenChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(params: any) {
        const items = Array.isArray(params) ? params : [params]
        let html = `<div style="font-weight:600;margin-bottom:4px">${items[0].axisValue}</div>`
        let total = 0
        for (const item of items) {
          total += item.value
          html += `<div style="display:flex;align-items:center;gap:6px">
            ${item.marker} ${item.seriesName}: <b>${item.value.toLocaleString()}</b>
          </div>`
        }
        html += `<div style="margin-top:4px;font-weight:600">合计: ${total.toLocaleString()}</div>`
        return html
      },
    },
    legend: {
      data: ['输入 Token', '输出 Token'],
      bottom: 0,
      textStyle: { fontSize: 12 },
    },
    grid: {
      left: 70,
      right: 20,
      top: 20,
      bottom: 40,
    },
    xAxis: {
      type: 'category',
      data: dates.map(d => d.slice(5)),
      axisLabel: { fontSize: 11, color: '#9ca3af' },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 11,
        color: '#9ca3af',
        formatter: (v: number) => formatTokens(v),
      },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [
      {
        name: '输入 Token',
        type: 'bar',
        stack: 'tokens',
        data: inputData,
        itemStyle: { borderRadius: [0, 0, 0, 0] },
        color: '#6366f1',
      },
      {
        name: '输出 Token',
        type: 'bar',
        stack: 'tokens',
        data: outputData,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        color: '#06b6d4',
        // 柱顶标签显示总数
        label: {
          show: true,
          position: 'top',
          formatter: (params: any) => {
            const idx = params.dataIndex
            const total = totalData[idx]
            return total > 0 ? formatTokens(total) : ''
          },
          fontSize: 10,
          color: '#6b7280',
        },
      },
    ],
  })
}

// 窗口 resize 自适应
function handleResize() {
  countChart?.resize()
  tokenChart?.resize()
}

onMounted(async () => {
  await loadModels()
  await loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  countChart?.dispose()
  tokenChart?.dispose()
  countChart = null
  tokenChart = null
})
</script>

<style scoped>
@import '../styles/dashboard-page.css';
</style>

