from langchain.tools import BaseTool
from langchain_community.chat_models.tongyi import ChatTongyi
from rag.embedding import get_embedding
from rag.vector_store import get_vector_store
from backend.config import get_settings

settings = get_settings()


class DocumentRAGTool(BaseTool):
    name: str = "document_qa"
    description: str = (
        "根据已上传的文档内容回答问题。\n"
        "使用前请确保用户已经上传了文档。\n"
        "输入: 关于文档内容的问题字符串"
    )

    session_id: str = "default"
    top_k: int = 5

    def _run(self, question: str) -> str:
        if not question.strip():
            return "请提供需要解答的问题"

        # 1. Generate query embedding
        try:
            embed_svc = get_embedding()
            query_embedding = embed_svc.embed_query(question)
        except Exception as e:
            return f"向量化失败: {str(e)}"

        # 2. Retrieve relevant chunks
        try:
            store = get_vector_store(f"session_{self.session_id}")
            results = store.search(query_embedding, top_k=self.top_k)
        except Exception as e:
            return f"文档检索失败: {str(e)}"

        if not results:
            return "未找到相关文档内容。请先上传文档后再提问。"

        # 3. Build context and generate answer
        context_parts = []
        for i, r in enumerate(results):
            context_parts.append(f"[文档片段{i+1}]\n{r['text']}")

        context = "\n\n".join(context_parts)

        # 4. LLM generate answer
        try:
            llm = ChatTongyi(
                model=settings.llm_model,
                dashscope_api_key=settings.dashscope_api_key,
                temperature=0.3,
            )

            prompt = f"""你是一个文档分析助手。请根据以下文档内容回答用户的问题。
如果文档内容不足以回答这个问题，请如实告知，不要编造信息。

【文档内容】
{context}

【用户问题】
{question}

请用清晰的语言回答，引用文档中的具体信息。"""

            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"生成回答失败: {str(e)}"

    async def _arun(self, question: str) -> str:
        return self._run(question)
