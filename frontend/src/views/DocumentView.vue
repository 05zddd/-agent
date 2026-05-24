<template>
  <div class="document-view">
    <div class="card">
      <h2 class="card-title">📄 文档问答</h2>
      <p class="hint">上传 PDF、Word、TXT 或图片文件，然后提问，我会从文档中检索答案。</p>

      <!-- Upload area -->
      <div
        class="upload-zone"
        @dragover.prevent
        @drop.prevent="handleDrop"
        :class="{ dragging }"
      >
        <input
          type="file"
          ref="fileInput"
          @change="handleFile"
          accept=".pdf,.docx,.doc,.txt,.md,.png,.jpg,.jpeg,.bmp,.tiff"
          style="display:none"
        />
        <div v-if="!uploading">
          <div class="upload-icon">📁</div>
          <p>拖拽文件到此处，或 <span class="link" @click="$refs.fileInput.click()">点击选择文件</span></p>
          <p class="upload-hint">支持 PDF / Word / TXT / 图片，最大 {{ maxSize }}MB</p>
        </div>
        <div v-else class="upload-progress">上传中...</div>
      </div>

      <div v-if="uploadStatus" :class="['status', uploadStatus.success ? 'success' : 'error']">
        {{ uploadStatus.message }}
      </div>

      <!-- Q&A area -->
      <div v-if="docs.length > 0" class="qa-section">
        <h3>文档知识问答</h3>
        <div class="qa-messages">
          <div v-for="(qa, idx) in qaList" :key="idx" class="qa-item">
            <div class="qa-q"><strong>Q:</strong> {{ qa.question }}</div>
            <div class="qa-a"><strong>A:</strong> {{ qa.answer }}</div>
          </div>
        </div>
        <div class="qa-input-area">
          <input
            v-model="question"
            @keyup.enter="askQuestion"
            placeholder="基于文档内容提问..."
            class="qa-input"
            :disabled="asking"
          />
          <button @click="askQuestion" :disabled="asking || !question.trim()" class="btn-ask">
            提问
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { uploadDocument, queryRAG } from '../api/index.js'

const maxSize = 20
const fileInput = ref(null)
const uploading = ref(false)
const uploadStatus = ref(null)
const docs = ref([])

const question = ref('')
const asking = ref(false)
const qaList = reactive([])

async function handleFile(e) {
  const file = e.target.files[0]
  if (file) await upload(file)
}

async function handleDrop(e) {
  const file = e.dataTransfer.files[0]
  if (file) await upload(file)
}

async function upload(file) {
  uploading.value = true
  uploadStatus.value = null
  try {
    const res = await uploadDocument(file)
    uploadStatus.value = { success: true, message: res.data.message }
    docs.value.push(res.data.doc_info || { filename: file.name })
  } catch (e) {
    uploadStatus.value = { success: false, message: '上传失败: ' + (e.response?.data?.detail || e.message) }
  } finally {
    uploading.value = false
  }
}

async function askQuestion() {
  if (!question.value.trim() || asking.value) return
  const q = question.value.trim()
  asking.value = true
  try {
    const res = await queryRAG(q)
    const results = res.data.results || []
    let answer = '未找到相关文档内容，请确认已上传文档。'
    if (results.length > 0) {
      answer = results.map((r, i) => `[片段${i+1}] ${r.text}`).join('\n\n')
    }
    qaList.push({ question: q, answer })
    question.value = ''
  } catch (e) {
    qaList.push({ question: q, answer: '查询失败: ' + (e.response?.data?.detail || e.message) })
  } finally {
    asking.value = false
  }
}
</script>

<style scoped>
.hint { color: var(--text-light); font-size: 0.9rem; margin-bottom: 16px; }
.upload-zone { border: 2px dashed var(--border); border-radius: 12px; padding: 40px; text-align: center; cursor: pointer; transition: all 0.2s; }
.upload-zone:hover { border-color: var(--primary); background: rgba(79,70,229,0.03); }
.upload-icon { font-size: 2.5rem; margin-bottom: 12px; }
.link { color: var(--primary); cursor: pointer; text-decoration: underline; }
.upload-hint { font-size: 0.8rem; color: var(--text-light); margin-top: 8px; }
.upload-progress { padding: 20px; color: var(--primary); }
.status { padding: 12px 16px; border-radius: 8px; margin-top: 12px; font-size: 0.9rem; }
.status.success { background: #f0fdf4; color: #16a34a; }
.status.error { background: #fef2f2; color: #dc2626; }

.qa-section { margin-top: 24px; }
.qa-section h3 { font-size: 1.05rem; margin-bottom: 12px; color: var(--text); }
.qa-messages { max-height: 400px; overflow-y: auto; margin-bottom: 16px; }
.qa-item { margin-bottom: 16px; padding: 12px; background: var(--bg); border-radius: 8px; }
.qa-q { margin-bottom: 8px; color: var(--primary); }
.qa-a { color: var(--text); line-height: 1.6; font-size: 0.9rem; white-space: pre-wrap; }
.qa-input-area { display: flex; gap: 10px; }
.qa-input { flex: 1; padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px; font-size: 0.95rem; outline: none; }
.qa-input:focus { border-color: var(--primary); }
.btn-ask { padding: 10px 20px; background: var(--primary); color: #fff; border: none; border-radius: 8px; cursor: pointer; }
.btn-ask:hover { background: var(--primary-light); }
.btn-ask:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
