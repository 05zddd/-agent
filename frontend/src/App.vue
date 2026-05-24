<template>
  <div class="app">
    <nav class="sidebar">
      <div class="logo">
        <h1>HelloAgents</h1>
        <span class="subtitle">智能助手</span>
      </div>
      <ul class="nav-links">
        <li>
          <router-link to="/" class="nav-item">
            <span class="icon">💬</span> 对话助手
          </router-link>
        </li>
        <li>
          <router-link to="/weather" class="nav-item">
            <span class="icon">🌤️</span> 天气查询
          </router-link>
        </li>
        <li>
          <router-link to="/trip" class="nav-item">
            <span class="icon">✈️</span> 行程规划
          </router-link>
        </li>
        <li>
          <router-link to="/document" class="nav-item">
            <span class="icon">📄</span> 文档问答
          </router-link>
        </li>
      </ul>
      <div class="sidebar-footer">
        <span>Powered by LangChain + DashScope</span>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style>
:root {
  --primary: #4f46e5;
  --primary-light: #6366f1;
  --bg: #f8fafc;
  --sidebar-bg: #1e293b;
  --card-bg: #ffffff;
  --text: #1e293b;
  --text-light: #64748b;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.app {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

.sidebar {
  width: 240px;
  background: var(--sidebar-bg);
  color: #fff;
  display: flex;
  flex-direction: column;
  padding: 24px 0;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 10;
}

.logo {
  padding: 0 20px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.logo h1 {
  font-size: 1.4rem;
  font-weight: 700;
  color: #fff;
}

.logo .subtitle {
  font-size: 0.85rem;
  color: rgba(255,255,255,0.5);
}

.nav-links {
  list-style: none;
  padding: 16px 12px;
  flex: 1;
}

.nav-item {
  display: block;
  padding: 10px 14px;
  border-radius: 8px;
  color: rgba(255,255,255,0.7);
  text-decoration: none;
  margin-bottom: 4px;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.nav-item:hover {
  background: rgba(255,255,255,0.1);
  color: #fff;
}

.nav-item.router-link-active {
  background: var(--primary);
  color: #fff;
}

.nav-item .icon {
  margin-right: 8px;
}

.sidebar-footer {
  padding: 16px 20px;
  font-size: 0.75rem;
  color: rgba(255,255,255,0.3);
  border-top: 1px solid rgba(255,255,255,0.1);
}

.main-content {
  margin-left: 240px;
  flex: 1;
  padding: 32px;
  max-width: 1000px;
  width: calc(100% - 240px);
}

.card {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  margin-bottom: 20px;
}

.card-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text);
}
</style>
