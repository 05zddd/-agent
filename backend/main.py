import sys
import os
import json
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import HumanMessage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_settings
from backend.models import ChatRequest, DocumentUploadResponse, DocumentInfo
from backend.database import (
    save_chat_message, get_chat_history, get_all_sessions,
    save_trip_record, save_document_record,
)
from backend.cache import cache
from backend.agent_builder import build_agent
from rag.loader import DocumentLoader
from rag.splitter import DocumentSplitter
from rag.embedding import get_embedding
from rag.vector_store import get_vector_store

settings = get_settings()

# Session-level agent cache
_agents: dict[str, object] = {}


def get_or_create_agent(session_id: str):
    if session_id not in _agents:
        _agents[session_id] = build_agent(session_id)
    return _agents[session_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await cache.connect()
    print(f"Redis connected: {cache.redis is not None}")
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    yield
    # Shutdown
    await cache.disconnect()


app = FastAPI(
    title="HelloAgents Trip Planner",
    description="LangChain + RAG 智能助手: 天气查询 · 行程规划 · 文档问答",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health ---

@app.get("/health")
async def health():
    return {"status": "ok", "service": "HelloAgents Trip Planner"}


# --- Chat (Agent) ---

@app.post("/api/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())[:8]

    # Save user message
    save_chat_message(session_id, "user", req.message)

    # Check cache — return cached reply directly (no need to stream)
    cached = await cache.get("chat", f"{session_id}:{req.message}")
    if cached:
        return {"reply": cached, "session_id": session_id}

    agent = get_or_create_agent(session_id)
    config = {"configurable": {"thread_id": session_id}}

    async def event_stream():
        full_reply = ""
        try:
            async for event in agent.astream_events(
                {"messages": [HumanMessage(content=req.message)]},
                config=config,
                version="v2",
            ):
                kind = event["event"]
                if kind == "on_tool_start":
                    tool_name = event["name"]
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name})}\n\n"
                elif kind == "on_tool_end":
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool': event['name']})}\n\n"
                elif kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        full_reply += chunk.content
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            if full_reply:
                save_chat_message(session_id, "assistant", full_reply)
                await cache.set("chat", f"{session_id}:{req.message}", full_reply)
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# --- Document Upload ---

@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), session_id: str = "default"):
    # Validate
    if not file.filename:
        raise HTTPException(400, "No file provided")

    if not DocumentLoader.is_supported(file.filename):
        raise HTTPException(400, f"Unsupported file type. Supported: {list(DocumentLoader.SUPPORTED_TYPES.keys())}")

    # Check size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(400, f"File too large: {size_mb:.1f}MB > {settings.max_file_size_mb}MB limit")

    # Save file
    os.makedirs("data/uploads", exist_ok=True)
    safe_name = f"{session_id}_{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join("data/uploads", safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Load and split
    try:
        text = DocumentLoader.load(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(500, f"Document parsing failed: {str(e)}")

    if not text.strip():
        os.remove(file_path)
        raise HTTPException(400, "Document contains no extractable text")

    # Split into chunks
    splitter = DocumentSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_with_metadata(text, {"session_id": session_id, "filename": file.filename})

    if not chunks:
        os.remove(file_path)
        raise HTTPException(400, "Document produced no text chunks")

    # Generate embeddings and store
    try:
        embed_svc = get_embedding()
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        embeddings = embed_svc.embed_texts(texts)

        store = get_vector_store(f"session_{session_id}")
        store.add_documents(texts=texts, embeddings=embeddings, metadatas=metadatas)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(500, f"Embedding/indexing failed: {str(e)}")

    # Save record
    file_type = DocumentLoader.get_type(file.filename)
    save_document_record(session_id, file.filename, file_type, file_path, len(chunks))

    return DocumentUploadResponse(
        success=True,
        message=f"文档 '{file.filename}' 上传成功，已分割为 {len(chunks)} 个文本块",
        doc_info=DocumentInfo(
            filename=file.filename,
            file_type=file_type or "unknown",
            size_bytes=len(content),
            chunks_count=len(chunks),
        ),
    )


@app.post("/api/rag/query")
async def rag_query(question: str, session_id: str = "default"):
    """Direct RAG query without going through the agent."""
    embed_svc = get_embedding()
    store = get_vector_store(f"session_{session_id}")
    query_embedding = embed_svc.embed_query(question)
    results = store.search(query_embedding, top_k=5)

    return {"results": results, "session_id": session_id, "count": len(results)}


# --- Weather (direct API, bypasses agent) ---

@app.get("/api/weather")
async def weather(city: str, extensions: str = "base"):
    from services.amap_service import get_amap
    try:
        amap = get_amap()
        data = amap.get_weather(city, extensions=extensions)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(500, str(e))


# --- Trip Planning (direct API) ---

@app.post("/api/trip/plan")
async def trip_plan(city: str, days: int = 3, preferences: str = "综合", start_date: str = "", session_id: str = "default"):
    from backend.tools.trip_tool import TripPlannerTool
    import json

    tool = TripPlannerTool()
    params = json.dumps({"city": city, "days": days, "preferences": preferences, "start_date": start_date})
    result = tool._run(params)

    # Save record
    save_trip_record(session_id, city, days, preferences, result)

    return {"success": True, "plan": result, "city": city, "days": days}


# --- Session history ---

@app.get("/api/sessions")
async def list_sessions():
    sessions = get_all_sessions()
    return {"sessions": sessions}


@app.get("/api/history/{session_id}")
async def history(session_id: str):
    msgs = get_chat_history(session_id)
    return {"session_id": session_id, "messages": msgs, "count": len(msgs)}


# --- Main ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
