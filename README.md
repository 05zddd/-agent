# HelloAgents Trip Planner

基于 **LangChain + RAG** 的单 Agent 智能助手，提供天气查询、行程规划、文档问答三大核心能力。

## 功能概览

| 功能 | 说明 |
|------|------|
| 天气查询 | 支持任意城市的实时天气和未来 3-4 天预报 |
| 行程规划 | 根据目的地、天数、偏好生成每日行程 + 注意事项 |
| 文档问答 | 上传 PDF / Word / TXT / 图片，自动解析并支持基于内容的问答 |
| 多轮对话 | Agent 统一入口，自动理解意图并调度对应工具 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Pydantic |
| LLM | LangChain + DashScope (qwen-max) |
| 向量库 | ChromaDB |
| 缓存 | Redis |
| 地图服务 | 高德地图 Web 服务 API + JavaScript API |
| 前端 | Vue 3 + Vite |
| 数据库 | SQLite |

## 架构

```
Vue 3 + Vite UI
 ├── 天气查询
 ├── 行程规划
 └── 文档上传/问答
        │
        ▼
LangChain Agent (ReAct)
 ├── WeatherTool    → 高德天气 API
 ├── TripPlannerTool → 高德 POI + LLM
 └── DocumentRAGTool → ChromaDB 向量检索 + LLM
        │
        ▼
RAG Pipeline
 Embedding (text-embedding-v4) → ChromaDB → Retrieve → Generate
        │
        ▼
Redis (缓存) + SQLite (持久化)
```

## 目录结构

```
helloagents-trip-planner/
├── backend/
│   ├── main.py              # FastAPI 服务入口 + 路由
│   ├── config.py            # Pydantic Settings 配置管理
│   ├── models.py            # 数据模型 (Pydantic + SQLAlchemy)
│   ├── database.py          # SQLite 数据库操作
│   ├── cache.py             # Redis 异步缓存层
│   ├── agent_builder.py     # LangChain Agent 组装工厂
│   └── tools/
│       ├── weather_tool.py  # 天气查询 Tool
│       ├── trip_tool.py     # 行程规划 Tool
│       └── doc_rag_tool.py  # 文档 RAG Tool
├── rag/
│   ├── loader.py            # 文档加载器 (PDF/Word/TXT/图片OCR)
│   ├── splitter.py          # 文本分块器
│   ├── embedding.py         # DashScope Embedding 服务
│   └── vector_store.py      # ChromaDB 向量存储与检索
├── services/
│   ├── amap_service.py      # 高德 API 封装 (天气/POI/地理编码)
│   └── ocr_service.py       # OCR 服务
├── frontend/
│   ├── src/
│   │   ├── App.vue          # 主布局 + 侧边导航
│   │   ├── main.js          # Vue Router 路由
│   │   ├── api/index.js     # Axios API 请求封装
│   │   └── views/
│   │       ├── ChatView.vue     # 智能对话
│   │       ├── WeatherView.vue  # 天气查询
│   │       ├── TripView.vue     # 行程规划
│   │       └── DocumentView.vue # 文档上传 + RAG 问答
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── data/
│   ├── uploads/             # 用户上传文档
│   └── chroma_db/           # ChromaDB 持久化数据
├── .env                     # 环境变量配置
├── requirements.txt         # Python 依赖
└── prompt.md                # 项目需求文档
```

## 快速开始

### 环境要求

- Python >= 3.10
- Node.js >= 18
- Redis (可选，不启动则跳过缓存)
- Tesseract (可选，仅图片 OCR 需要)

### 1. 配置 API Keys

编辑项目根目录下的 `.env` 文件：

```env
# 阿里云 DashScope (必填)
DASHSCOPE_API_KEY=your_dashscope_api_key
LLM_MODEL=qwen-max

# 高德地图 (必填)
AMAP_API_KEY=your_amap_web_service_key
AMAP_JS_API_KEY=your_amap_js_api_key
```

> **获取 API Key：**
> - DashScope：[阿里云百炼平台](https://bailian.console.aliyun.com/) → 模型广场 → API-KEY 管理
> - 高德地图：[高德开放平台](https://console.amap.com/dev/key/app) → 创建应用 → 获取 Key（Web服务 + Web端JS API）

### 2. 安装后端依赖

```bash
# 使用 uv (推荐)
uv venv
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### 3. 启动后端

```bash
# 激活虚拟环境后
python -m backend.main

# 或直接使用 uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

后端运行在 `http://localhost:8000`，可访问 `/docs` 查看 Swagger API 文档。

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 `http://localhost:3000`，通过 Vite proxy 自动转发 API 请求到后端。

## API 接口

### 对话（Agent 统一入口）

```
POST /api/chat
Content-Type: application/json

{
  "message": "北京今天天气怎么样？",
  "session_id": "default"
}
```

### 天气查询（直连 API）

```
GET /api/weather?city=上海&extensions=all
```

参数：
- `city` (必填) — 城市名或行政区划代码
- `extensions` — `base` (实时) / `all` (预报)，默认 `base`

### 行程规划（直连 API）

```
POST /api/trip/plan?city=杭州&days=3&preferences=自然风光&start_date=2026-06-01
```

参数：
- `city` (必填) — 目的地城市
- `days` — 天数，默认 3
- `preferences` — 偏好：`自然风光` / `美食` / `历史文化` / `购物` / `亲子` / `休闲` / `综合`
- `start_date` — 出发日期，格式 `YYYY-MM-DD`

### 文档上传

```
POST /api/documents/upload?session_id=default
Content-Type: multipart/form-data

file: (binary)
```

支持格式：`.pdf` `.docx` `.txt` `.md` `.png` `.jpg` `.jpeg` `.bmp` `.tiff`

### RAG 查询

```
POST /api/rag/query?question=文档中提到了哪些关键信息&session_id=default
```

### 会话历史

```
GET /api/history/{session_id}
```

## 配置参考

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key | - |
| `LLM_MODEL` | 大模型名称 | `qwen-max` |
| `AMAP_API_KEY` | 高德 Web 服务 Key | - |
| `AMAP_JS_API_KEY` | 高德 JavaScript API Key | - |
| `EMBEDDING_MODEL` | Embedding 模型 | `text-embedding-v4` |
| `CHROMA_PERSIST_DIR` | ChromaDB 持久化目录 | `./data/chroma_db` |
| `REDIS_HOST` | Redis 地址 | `localhost` |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `CACHE_TTL` | 缓存过期时间 (秒) | `3600` |
| `DATABASE_URL` | SQLite 数据库路径 | `sqlite:///./data/trip_planner.db` |
| `HOST` | 服务绑定地址 | `0.0.0.0` |
| `PORT` | 服务端口 | `8000` |
| `MAX_FILE_SIZE_MB` | 上传文件大小限制 | `20` |

## 使用示例

### 天气查询

```
用户: 杭州今天天气怎么样？
助手: 【杭州市 实时天气】
      天气: 晴
      温度: 26°C
      风向: 东南风 2级
      湿度: 65%
      发布时间: 2026-05-24 14:00:00
```

### 行程规划

```
用户: 帮我规划一个3天的西安行程，喜欢历史文化
助手: (生成完整的3天行程，包含上午/下午/晚上安排、天气提醒、交通和饮食建议)
```

### 文档问答

```
1. 用户在"文档问答"页面拖入一份项目报告 PDF
2. 系统自动解析、分块、向量化存储
3. 用户提问: 报告中的核心指标是什么？
4. 系统检索相关片段并生成回答
```

## 注意事项

- 高德天气 API 和 POI 搜索共用一个 Web 服务 Key，前端地图需额外申请 JavaScript API Key
- Embedding 模型直接调用 DashScope API，与 LLM 共用 API Key
- 天气数据和 POI 搜索结果会自动缓存到 Redis，避免重复调用消耗 API 配额
- 图片 OCR 需要系统安装 Tesseract 才能正常使用
- ChromaDB 适合开发和小规模使用，生产环境建议迁移至 Milvus 或 Pinecone
