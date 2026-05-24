import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import ChatView from './views/ChatView.vue'
import WeatherView from './views/WeatherView.vue'
import TripView from './views/TripView.vue'
import DocumentView from './views/DocumentView.vue'

const routes = [
  { path: '/', name: 'chat', component: ChatView },
  { path: '/weather', name: 'weather', component: WeatherView },
  { path: '/trip', name: 'trip', component: TripView },
  { path: '/document', name: 'document', component: DocumentView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(router)
app.mount('#app')
