<template>
  <div class="weather-view">
    <div class="card">
      <h2 class="card-title">🌤️ 天气查询</h2>

      <div class="search-bar">
        <input
          v-model="city"
          @keyup.enter="queryWeather('base')"
          placeholder="输入城市名称，如：北京、上海、杭州..."
          class="search-input"
        />
        <button @click="queryWeather('base')" :disabled="loading" class="btn">实时天气</button>
        <button @click="queryWeather('all')" :disabled="loading" class="btn btn-outline">天气预报</button>
      </div>

      <div v-if="data && mode === 'base'" class="weather-card live">
        <div class="weather-main">
          <div class="temp">{{ live.temperature }}°C</div>
          <div class="condition">{{ live.weather }}</div>
        </div>
        <div class="weather-details">
          <div class="detail"><span class="label">湿度</span><span>{{ live.humidity }}%</span></div>
          <div class="detail"><span class="label">风向</span><span>{{ live.winddirection }}</span></div>
          <div class="detail"><span class="label">风力</span><span>{{ live.windpower }}级</span></div>
          <div class="detail"><span class="label">发布时间</span><span>{{ live.reporttime }}</span></div>
        </div>
      </div>

      <div v-if="data && mode === 'all'" class="forecast-list">
        <h3>{{ data.forecasts?.[0]?.city || city }} 未来天气预报</h3>
        <div v-for="(cast, i) in (data.forecasts?.[0]?.casts || [])" :key="i" class="forecast-card">
          <div class="forecast-date">{{ cast.date }} {{ weekMap[cast.week] || '' }}</div>
          <div class="forecast-day">
            <span>白天: {{ cast.dayweather }} {{ cast.daytemp }}°C</span>
            <span class="wind">{{ cast.daywind }}{{ cast.daypower }}级</span>
          </div>
          <div class="forecast-night">
            <span>夜间: {{ cast.nightweather }} {{ cast.nighttemp }}°C</span>
            <span class="wind">{{ cast.nightwind }}{{ cast.nightpower }}级</span>
          </div>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { getWeather } from '../api/index.js'

const weekMap = { '1': '周一', '2': '周二', '3': '周三', '4': '周四', '5': '周五', '6': '周六', '7': '周日' }

const city = ref('')
const data = ref(null)
const mode = ref('base')
const live = ref({})
const loading = ref(false)
const error = ref('')

async function queryWeather(m) {
  if (!city.value.trim()) return
  loading.value = true
  mode.value = m
  error.value = ''
  try {
    const res = await getWeather(city.value.trim(), m)
    data.value = res.data.data
    if (m === 'base' && res.data.data?.lives) {
      live.value = res.data.data.lives[0]
    }
  } catch (e) {
    error.value = '查询失败: ' + (e.response?.data?.detail || e.message)
    data.value = null
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.search-bar { display: flex; gap: 10px; margin-bottom: 24px; }
.search-input { flex: 1; padding: 12px 16px; border: 1px solid var(--border); border-radius: 8px; font-size: 0.95rem; outline: none; }
.search-input:focus { border-color: var(--primary); }
.btn { padding: 12px 20px; background: var(--primary); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 0.9rem; }
.btn:hover { background: var(--primary-light); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-outline { background: transparent; color: var(--primary); border: 1px solid var(--primary); }
.btn-outline:hover { background: var(--primary); color: #fff; }

.weather-card.live { text-align: center; }
.weather-main { margin-bottom: 24px; }
.temp { font-size: 4rem; font-weight: 700; color: var(--text); }
.condition { font-size: 1.3rem; color: var(--text-light); margin-top: 4px; }
.weather-details { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.detail { display: flex; flex-direction: column; gap: 4px; }
.detail .label { font-size: 0.8rem; color: var(--text-light); text-transform: uppercase; }

.forecast-list h3 { margin-bottom: 16px; }
.forecast-card { padding: 14px; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; }
.forecast-date { font-weight: 600; margin-bottom: 6px; }
.forecast-day, .forecast-night { display: flex; justify-content: space-between; font-size: 0.9rem; color: var(--text-light); }
.wind { color: var(--text-light); font-size: 0.85rem; }
.error { color: #dc2626; padding: 16px; background: #fef2f2; border-radius: 8px; }
</style>
