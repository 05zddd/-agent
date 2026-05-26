import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export function sendMessage(message, sessionId = 'default') {
  return api.post('/chat', { message, session_id: sessionId })
}

export async function* streamMessage(message, sessionId = 'default') {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(err.detail || `HTTP ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          yield JSON.parse(line.slice(6))
        } catch {
          // skip malformed JSON lines
        }
      }
    }
  }
}

export function getWeather(city, extensions = 'base') {
  return api.get('/weather', { params: { city, extensions } })
}

export function planTrip(city, days, preferences, startDate = '', sessionId = 'default') {
  return api.post('/trip/plan', null, {
    params: { city, days, preferences, start_date: startDate, session_id: sessionId }
  })
}

export function uploadDocument(file, sessionId = 'default') {
  const form = new FormData()
  form.append('file', file)
  form.append('session_id', sessionId)
  return api.post('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function queryRAG(question, sessionId = 'default') {
  return api.post('/rag/query', null, { params: { question, session_id: sessionId } })
}

export function getHistory(sessionId) {
  return api.get(`/history/${sessionId}`)
}

export function getSessions() {
  return api.get('/sessions')
}
