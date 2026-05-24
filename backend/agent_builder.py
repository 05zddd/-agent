from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.chat_models.tongyi import ChatTongyi
from backend.tools.weather_tool import WeatherTool
from backend.tools.trip_tool import TripPlannerTool
from backend.tools.doc_rag_tool import DocumentRAGTool
from backend.config import get_settings

settings = get_settings()

SYSTEM_MESSAGE = """你是一个智能助手，具备以下能力：
1. 天气查询 - 查询城市实时天气和天气预报，使用 weather_query 工具
2. 行程规划 - 规划旅行行程，提供详细的每日安排和注意事项，使用 trip_planner 工具
3. 文档问答 - 分析用户上传的文档内容并回答相关问题，使用 document_qa 工具

重要规则：
- 对于行程规划类请求，调用行程规划工具后，请主动调用天气查询工具获取目的地天气
- 对于文档问答类请求，请先确认用户已上传文档
- 天气查询工具输入格式: "城市名,base" 或 "城市名,all"
- 行程规划工具输入格式为JSON: {"city":"城市名","days":天数,"preferences":"偏好","start_date":"日期"}
- 回复时用清晰的中文，行程规划结果请用 markdown 格式组织"""


def build_agent(session_id: str = "default"):
    """Build a LangChain agent with tools and memory for a given session.

    Args:
        session_id: Session identifier for memory isolation

    Returns:
        Compiled LangGraph agent graph
    """
    llm = ChatTongyi(
        model=settings.llm_model,
        dashscope_api_key=settings.dashscope_api_key,
        temperature=0.7,
    )

    tools = [
        WeatherTool(),
        TripPlannerTool(),
        DocumentRAGTool(session_id=session_id),
    ]

    checkpointer = MemorySaver()

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_MESSAGE,
        checkpointer=checkpointer,
    )

    return agent


def create_llm(temperature: float = 0.7):
    """Create a standalone LLM instance (not wrapped in agent)."""
    return ChatTongyi(
        model=settings.llm_model,
        dashscope_api_key=settings.dashscope_api_key,
        temperature=temperature,
    )
