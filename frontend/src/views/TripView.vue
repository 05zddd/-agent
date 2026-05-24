<template>
  <div class="trip-view">
    <div class="card">
      <h2 class="card-title">✈️ 行程规划</h2>

      <div class="trip-form">
        <div class="form-row">
          <div class="form-group">
            <label>目的地城市</label>
            <input v-model="form.city" placeholder="如：杭州、西安..." class="form-input" />
          </div>
          <div class="form-group short">
            <label>天数</label>
            <input v-model.number="form.days" type="number" min="1" max="14" class="form-input" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>偏好</label>
            <div class="tags">
              <span
                v-for="p in preferences"
                :key="p"
                :class="['tag', { active: form.preferences === p }]"
                @click="form.preferences = p"
              >{{ p }}</span>
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>出发日期（可选）</label>
            <input v-model="form.startDate" type="date" class="form-input" />
          </div>
        </div>
        <button @click="planTrip" :disabled="loading || !form.city" class="btn-plan">
          {{ loading ? '规划中...' : '开始规划' }}
        </button>
      </div>

      <div v-if="result" class="result" v-html="renderMarkdown(result)"></div>
      <div v-if="error" class="error">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { planTrip as planTripApi } from '../api/index.js'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ breaks: true, linkify: true })

const preferences = ['自然风光', '美食', '历史文化', '购物', '亲子', '休闲', '综合']

const form = reactive({
  city: '',
  days: 3,
  preferences: '综合',
  startDate: '',
})

const loading = ref(false)
const result = ref('')
const error = ref('')

function renderMarkdown(text) {
  return md.render(text)
}

async function planTrip() {
  if (!form.city.trim()) return
  loading.value = true
  error.value = ''
  result.value = ''
  try {
    const res = await planTripApi(
      form.city.trim(),
      form.days,
      form.preferences,
      form.startDate
    )
    result.value = res.data.plan
  } catch (e) {
    error.value = '规划失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.trip-form { margin-bottom: 24px; }
.form-row { display: flex; gap: 16px; margin-bottom: 16px; }
.form-group { flex: 1; }
.form-group.short { max-width: 120px; }
.form-group label { display: block; margin-bottom: 6px; font-size: 0.85rem; font-weight: 500; color: var(--text); }
.form-input { width: 100%; padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px; font-size: 0.95rem; outline: none; }
.form-input:focus { border-color: var(--primary); }
.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tag { padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border); cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }
.tag.active { background: var(--primary); color: #fff; border-color: var(--primary); }
.tag:hover:not(.active) { border-color: var(--primary); color: var(--primary); }
.btn-plan { padding: 14px 32px; background: var(--primary); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; width: 100%; }
.btn-plan:hover { background: var(--primary-light); }
.btn-plan:disabled { opacity: 0.5; cursor: not-allowed; }

.result { margin-top: 24px; padding: 20px; background: var(--bg); border-radius: 8px; line-height: 1.8; }
.result :deep(h2) { font-size: 1.1rem; margin: 16px 0 8px; color: var(--primary); }
.result :deep(h3) { font-size: 1rem; margin: 12px 0 6px; }
.result :deep(ul), .result :deep(ol) { padding-left: 20px; }
.result :deep(li) { margin-bottom: 4px; }
.result :deep(strong) { color: var(--text); }
.error { color: #dc2626; padding: 16px; background: #fef2f2; border-radius: 8px; }
</style>
