<template>
  <div class="chat-view">
    <!-- History Sidebar -->
    <aside class="history-panel">
      <div class="history-header">
        <h3>历史会话</h3>
        <button @click="newChat" class="btn-new">＋ 新对话</button>
      </div>
      <div class="history-list">
        <div v-if="sessions.length === 0" class="no-history">暂无历史会话</div>
        <div
          v-for="s in sessions"
          :key="s.session_id"
          :class="['history-item', { active: s.session_id === sessionId }]"
          @click="loadSession(s.session_id)"
        >
          <div class="session-name">{{ s.session_id }}</div>
          <span class="session-count">{{ s.msg_count }} 条</span>
        </div>
      </div>
      <div class="history-footer">
        <button @click="refreshSessions" class="btn-refresh">刷新列表</button>
      </div>
    </aside>

    <!-- Chat Area -->
    <div class="card chat-container">
      <div class="chat-top">
        <h2 class="card-title">💬 智能对话助手</h2>
        <span class="session-badge">会话: {{ sessionId }}</span>
      </div>
      <p class="hint">我可以帮你查天气、规划行程、分析文档。直接跟我说吧！</p>

      <div class="chat-messages" ref="msgContainer">
        <div v-if="messages.length === 0" class="empty-state">
          开始新对话吧～
        </div>
        <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
          <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
          <div class="message-bubble" v-html="renderMarkdown(msg.content)"></div>
        </div>
        <div v-if="loading" class="message assistant">
          <div class="message-avatar">🤖</div>
          <div class="message-bubble typing">思考中...</div>
        </div>
      </div>

      <div class="chat-input-area">
        <input
          v-model="input"
          @keyup.enter="send"
          placeholder="输入你的问题..."
          :disabled="loading"
          class="chat-input"
        />
        <button @click="send" :disabled="loading || !input.trim()" class="btn-send">
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { sendMessage, getHistory, getSessions } from '../api/index.js'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ breaks: true, linkify: true })

const messages = ref([])
const input = ref('')
const loading = ref(false)
const sessionId = ref('default')
const sessions = ref([])
const msgContainer = ref(null)

onMounted(() => { refreshSessions() })

function renderMarkdown(text) { return md.render(text) }

async function refreshSessions() {
  try {
    const res = await getSessions()
    sessions.value = res.data.sessions || []
  } catch (e) { /* ignore */ }
}

async function loadSession(sid) {
  sessionId.value = sid
  try {
    const res = await getHistory(sid)
    messages.value = res.data.messages.map(m => ({
      role: m.role,
      content: m.content,
    }))
  } catch (e) {
    messages.value = []
  }
  await nextTick()
  scrollBottom()
}

function newChat() {
  const id = 'chat_' + Date.now().toString(36)
  sessionId.value = id
  messages.value = []
}

async function send() {
  if (!input.value.trim() || loading.value) return

  const msg = input.value.trim()
  messages.value.push({ role: 'user', content: msg })
  input.value = ''
  loading.value = true

  try {
    const res = await sendMessage(msg, sessionId.value)
    const returnedId = res.data.session_id || sessionId.value
    if (sessionId.value !== returnedId) {
      sessionId.value = returnedId
    }
    messages.value.push({ role: 'assistant', content: res.data.reply })
    refreshSessions()
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      content: '出错了：' + (e.response?.data?.detail || e.message),
    })
  } finally {
    loading.value = false
    await nextTick()
    scrollBottom()
  }
}

function scrollBottom() {
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-view {
  display: flex;
  gap: 20px;
  height: calc(100vh - 100px);
}

/* History Panel */
.history-panel {
  width: 220px;
  min-width: 220px;
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}
.history-header {
  padding: 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.history-header h3 { font-size: 0.95rem; }
.btn-new {
  padding: 4px 10px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  white-space: nowrap;
}
.btn-new:hover { background: var(--primary-light); }
.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.no-history {
  text-align: center;
  color: var(--text-light);
  font-size: 0.85rem;
  padding: 30px 0;
}
.history-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.15s;
}
.history-item:hover { background: var(--bg); }
.history-item.active { background: #eef2ff; color: var(--primary); }
.session-name {
  font-size: 0.85rem;
  font-weight: 500;
  word-break: break-all;
}
.session-count {
  font-size: 0.75rem;
  color: var(--text-light);
}
.history-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--border);
}
.btn-refresh {
  width: 100%;
  padding: 6px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--text-light);
}
.btn-refresh:hover { background: var(--bg); }

/* Chat */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}
.chat-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.session-badge {
  font-size: 0.75rem;
  background: var(--bg);
  padding: 4px 10px;
  border-radius: 12px;
  color: var(--text-light);
}
.hint { color: var(--text-light); font-size: 0.9rem; margin-bottom: 16px; }
.chat-messages { flex: 1; overflow-y: auto; padding: 16px 0; }
.empty-state { text-align: center; color: var(--text-light); padding: 60px 0; }
.message { display: flex; gap: 10px; margin-bottom: 20px; }
.message.user { flex-direction: row-reverse; }
.message-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg); font-size: 1.1rem; flex-shrink: 0;
}
.message-bubble {
  max-width: 75%; padding: 12px 16px; border-radius: 12px;
  line-height: 1.6; font-size: 0.95rem;
}
.message.user .message-bubble {
  background: var(--primary); color: #fff; border-bottom-right-radius: 4px;
}
.message.assistant .message-bubble {
  background: var(--bg); border-bottom-left-radius: 4px;
}
.message-bubble :deep(h2) { font-size: 1.1rem; margin: 8px 0 4px; }
.message-bubble :deep(h3) { font-size: 1rem; margin: 6px 0 3px; }
.message-bubble :deep(ul), .message-bubble :deep(ol) { padding-left: 20px; }
.message-bubble :deep(code) {
  background: rgba(0,0,0,0.08); padding: 2px 6px; border-radius: 4px; font-size: 0.85rem;
}
.message-bubble :deep(pre) {
  background: #1e293b; color: #e2e8f0; padding: 12px; border-radius: 8px; overflow-x: auto; margin: 8px 0;
}
.typing { color: var(--text-light); font-style: italic; }
.chat-input-area {
  display: flex; gap: 10px; padding-top: 16px; border-top: 1px solid var(--border);
}
.chat-input {
  flex: 1; padding: 12px 16px; border: 1px solid var(--border);
  border-radius: 8px; font-size: 0.95rem; outline: none;
}
.chat-input:focus { border-color: var(--primary); }
.btn-send {
  padding: 12px 24px; background: var(--primary); color: #fff;
  border: none; border-radius: 8px; cursor: pointer; font-size: 0.95rem;
}
.btn-send:hover { background: var(--primary-light); }
.btn-send:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
