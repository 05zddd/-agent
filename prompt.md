# LangChain + RAG 智能助手项目 Prompt

## 一、项目概述

### 1.1 项目定位

构建一个基于 **LangChain + RAG** 的单 Agent 智能助手。核心能力：

- **天气查询**：支持查询任意城市的实时天气和预报
- **行程规划**：根据目的地、日期、偏好生成行程安排和注意事项
- **文档识别**：上传 PDF/Word/TXT/图片，自动解析内容并支持问答

### 1.2 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Pydantic |
| LLM | LangChain + DashScope (qwen-max) |
| 向量库 | ChromaDB |
| 缓存 | Redis |
| 外部服务 | HTTPX + 高德地图 Web 服务 + 高德 JavaScript API |
| 前端 | Vue 3 + Vite |
| 数据库 | SQLite |

---

## 二、架构设计

### 2.1 整体架构（单 Agent）

```
┌─────────────────────────────────────────────────┐
│                  Vue 3 + Vite UI                   │
│    ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│    │ 天气查询  │  │ 行程规划  │  │ 文档上传/问答│  │
│    └────┬─────┘  └────┬─────┘  └──────┬──────┘  │
├─────────┼──────────────┼───────────────┼─────────┤
│         ▼              ▼               ▼         │
│  ┌─────────────────────────────────────────────┐ │
│  │           LangChain Agent                    │ │
│  │                                              │ │
│  │  ┌──────────┐ ┌───────────┐ ┌────────────┐  │ │
│  │  │Weather   │ │Trip       │ │Document    │  │ │
│  │  │Tool      │ │Planner    │ │RAG Tool    │  │ │
│  │  │          │ │Tool       │ │            │  │ │
│  │  └────┬─────┘ └─────┬─────┘ └──────┬─────┘  │ │
│  │       │             │              │        │ │
│  │       ▼             ▼              ▼        │ │
│  │  ┌───────────────────────────────────────┐  │ │
│  │  │         Tool Executor                  │  │ │
│  │  │  高德天气API / 高德POI / 向量检索      │  │ │
│  │  └───────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────┘ │
│                        │                         │
│                        ▼                         │
│  ┌─────────────────────────────────────────────┐ │
│  │              RAG Pipeline                    │ │
│  │  Embedding → ChromaDB → Retrieve ────────── │ │
│  │                    │                         │ │
│  │  ┌──────────┐  ┌──────────┐                 │ │
│  │  │  Redis   │  │  SQLite  │                 │ │
│  │  │ (Cache)  │  │  (DB)    │                 │ │
│  │  └──────────┘  └──────────┘                 │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 2.2 关键技术点

| 项目 | 说明 |
|------|------|
| **单Agent** | 一个 LangChain Agent，统一调度所有 Tool |
| **Tool机制** | 天气、行程、文档各封装为独立 Tool |
| **RAG** | 文档上传后分块→Embedding→Chroma，查询时检索+生成 |
| **多轮对话记忆** | ConversationBufferMemory 保持上下文 |
| **Prompt 路由** | Intent 识别，自动选择合适工具链 |

---

## 三、详细功能设计

### 3.1 天气查询

**输入**：`"北京今天天气怎么样？"` 或 `"上海未来三天有雨吗？"`

**流程**：
```
用户输入 → Agent → WeatherTool → 高德天气API → Agent → 格式化输出
```

**高德天气 API**：
- 地址：`https://restapi.amap.com/v3/weather/weatherInfo`
- 参数：`city`(城市编码/adcode) + `extensions=all`(预报) / `base`(实时)
- 返回：实时温度、湿度、风力、未来预报

**Tool 代码骨架**：
```python
from langchain.tools import BaseTool
import httpx

class WeatherTool(BaseTool):
    name = "weather_query"
    description = "查询指定城市的天气。输入格式: 城市名,查询类型(base=实时/all=预报)"

    def _run(self, query: str) -> str:
        # 解析城市名 + 类型
        # 调用高德天气 API (httpx)
        # 返回格式化的天气信息
        ...
```

### 3.2 行程规划

**输入**：`"帮我规划一个3天的杭州行程，喜欢自然风光和美食"`

**流程**：
```
用户输入 → Agent → TripPlannerTool
    ├── 高德POI搜索景点
    ├── 高德天气(出行日期)
    └── LLM生成行程 + 注意事项
→ Agent → 结构化行程输出
```

**Tool 代码骨架**：
```python
class TripPlannerTool(BaseTool):
    name = "trip_planner"
    description = "规划旅行行程。输入JSON: {city, days, preferences, start_date}"

    def _run(self, query: str) -> str:
        # 1. 解析用户需求
        # 2. 调用高德POI搜索景点/酒店
        # 3. 查询天气预报
        # 4. LLM生成每日行程
        # 5. 生成注意事项(天气、交通、饮食)
        ...
```

**输出格式要求**：
- 每天分上午/下午/晚上三段
- 景点间考虑距离和交通
- 注意事项独立成节（天气提醒、穿着建议、饮食注意、安全提示）

### 3.3 文档识别 + RAG

**输入**：用户上传 PDF/Word/TXT/图片，然后提问

**流程**：
```
文件上传 → DocumentLoader → 文本清洗 → TextSplitter(500chunk/50overlap)
    → Embedding(text-embedding-v4) → ChromaDB向量存储
    → 用户提问 → 向量检索(top-k=5) → LLM生成回答
```

**支持格式**：

| 格式 | 解析库 |
|------|--------|
| PDF | `PyMuPDF` (pdfplumber备选) |
| Word (.docx) | `python-docx` |
| TXT | 直接读取 |
| 图片 | `pytesseract` OCR + `Pillow` |

**RAG Tool 代码骨架**：
```python
class DocumentRAGTool(BaseTool):
    name = "document_qa"
    description = "根据上传的文档内容回答问题"

    def _run(self, question: str) -> str:
        # 1. 问题向量化
        # 2. 从Chroma检索相关文档块 (top-k=5)
        # 3. 拼接prompt: "根据以下文档内容回答：{docs}\n\n问题：{question}"
        # 4. LLM生成答案
        ...
```

### 3.4 Agent 组装

```python
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models.tongyi import ChatTongyi

# LLM (DashScope qwen-max)
llm = ChatTongyi(
    model="qwen-max",
    dashscope_api_key="sk-xxx"
)

# Tools
tools = [WeatherTool(), TripPlannerTool(), DocumentRAGTool()]

# Memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Agent (ReAct模式)
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    memory=memory,
    verbose=True,
    system_message="""你是一个智能助手，具备以下能力：
1. 天气查询 - 查询城市实时天气和预报
2. 行程规划 - 规划旅行行程，提供注意事项
3. 文档问答 - 分析上传的文档并回答问题

对于行程规划类请求，请主动调用天气工具查询目的地的天气。
对于文档类请求，请先确认用户已上传文档。"""
)
```

---

## 四、项目目录结构

```
helloagents-trip-planner/
├── frontend/                   # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── components/         # 天气卡片、行程时间线、文档上传区
│   │   ├── views/              # 页面视图
│   │   └── api/                # HTTPX 请求封装
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── backend/
│   ├── main.py                 # FastAPI 服务入口
│   ├── config.py               # 配置管理(.env) — Pydantic Settings
│   ├── models.py               # Pydantic 数据模型
│   ├── database.py             # SQLite 数据库操作
│   ├── cache.py                # Redis 缓存层
│   ├── agent_builder.py        # Agent 组装工厂
│   └── tools/
│       ├── __init__.py
│       ├── weather_tool.py     # 天气查询 Tool (httpx)
│       ├── trip_tool.py        # 行程规划 Tool (httpx + 高德POI)
│       └── doc_rag_tool.py     # 文档RAG Tool
├── rag/
│   ├── loader.py               # 文档加载器(PDF/Word/TXT/OCR)
│   ├── splitter.py             # 文本分块
│   ├── embedding.py            # 向量化 (DashScope text-embedding-v4)
│   └── vector_store.py         # ChromaDB存储与检索
├── services/
│   ├── amap_service.py         # 高德API封装(天气+POI) — httpx
│   └── ocr_service.py          # OCR服务(图片识别)
├── data/
│   ├── uploads/                # 用户上传的文档
│   └── chroma_db/              # ChromaDB持久化
├── .env                        # API Keys等配置
├── requirements.txt
└── prompt.md                   # 本文件
```

---

## 五、关键配置 .env

```env
# LLM (DashScope)
DASHSCOPE_API_KEY=your_api_key
LLM_MODEL=qwen-max

# 高德地图
AMAP_API_KEY=your_amap_key
AMAP_JS_API_KEY=your_amap_js_key   # 高德 JavaScript API (前端地图)

# Embedding模型 (DashScope)
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_API_KEY=same_as_dashscope  # 与 DASHSCOPE_API_KEY 共用

# 向量库 (ChromaDB)
CHROMA_PERSIST_DIR=./data/chroma_db

# Redis 缓存
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CACHE_TTL=3600                    # 缓存过期时间(秒)

# SQLite 数据库
DATABASE_URL=sqlite:///./data/trip_planner.db

# 服务端口
HOST=0.0.0.0
PORT=8000

# 文档限制
MAX_FILE_SIZE_MB=20
```

---

## 六、开发步骤建议

### Phase 1：骨架搭建（1天）
- [ ] 项目目录创建 + `requirements.txt`
- [ ] `config.py` — Pydantic Settings 读取 .env 配置
- [ ] FastAPI `main.py` — 基础路由 `/health`
- [ ] SQLite 数据库初始化 + Redis 连接测试

### Phase 2：Tool 开发（2-3天）
- [ ] `WeatherTool` — HTTPX + 高德天气 API + 测试
- [ ] `TripPlannerTool` — HTTPX + POI搜索 + 行程生成 + 注意事项
- [ ] Redis 缓存接入（天气数据、POI搜索结果）
- [ ] 独立测试每个 Tool，确保调用正常

### Phase 3：RAG Pipeline（2天）
- [ ] 文档加载器（PDF/Word/TXT）
- [ ] 文本分块 + Embedding
- [ ] ChromaDB 向量存储 + 检索
- [ ] `DocumentRAGTool` 封装 + 流式输出

### Phase 4：Agent 组装（1天）
- [ ] Agent + Tools + Memory 组装 (LangChain + DashScope qwen-max)
- [ ] 多轮对话测试
- [ ] Prompt 调优（Intent 识别准确率）

### Phase 5：前端 + 集成（2天）
- [ ] Vue 3 + Vite 项目初始化
- [ ] 前端页面开发（天气卡片、行程时间线、文档上传区）
- [ ] 高德 JavaScript API 地图组件集成
- [ ] FastAPI 路由对接 + 前后端联调

### Phase 6：优化（1-2天）
- [ ] RAG 检索质量调优（rerank、chunk大小）
- [ ] Redis 缓存策略优化
- [ ] 错误处理 + fallback
- [ ] 日志 + 监控

---

## 七、注意事项

1. **高德API Key**：天气 API 和 POI 搜索共用一个 Web 服务 Key；前端地图需额外申请 JavaScript API Key
2. **Embedding 模型**：直接调用 DashScope 的 `text-embedding-v4`，无需本地部署，与 LLM 共用 API Key
3. **ChromaDB 持久化**：生产环境建议用 Milvus 或 Pinecone 替代
4. **Redis 缓存**：天气数据、POI搜索结果建议缓存，避免重复调用高德API（注意配额限制）
5. **SQLite**：存储用户查询历史、行程记录，生产环境可迁移至 PostgreSQL
6. **HTTPX**：统一使用 HTTPX 异步客户端调用外部服务，支持超时、重试配置
7. **文档大小**：大文档需异步处理，避免阻塞主线程
8. **安全**：文档上传需校验文件类型和大小，防止恶意文件
9. **Token 管理**：长文档需做摘要压缩，避免超出 context window
10. **Agent 输出格式**：行程规划结果建议用 JSON 结构化，方便前端 Vue 组件渲染时间线

---

## 八、扩展方向（可选）

- [ ] 语音输入（Whisper STT）
- [ ] 多用户 + 历史记录
- [ ] 行程分享 / 导出 PDF
- [ ] 实时交通 + 路线规划
- [ ] 多模态文档（表格、图表识别）
- [ ] Agent 工具自动发现（Tool self-selection）
