import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export function sendMessage(message, sessionId = 'default') {
  return api.post('/chat', { message, session_id: sessionId })
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
