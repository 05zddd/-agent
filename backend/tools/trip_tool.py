import json
from langchain.tools import BaseTool
from langchain_community.chat_models.tongyi import ChatTongyi
from services.amap_service import get_amap
from backend.config import get_settings

settings = get_settings()


class TripPlannerTool(BaseTool):
    name: str = "trip_planner"
    description: str = (
        "规划旅行行程，根据目的地、天数、偏好生成详细的每日行程和注意事项。\n"
        "输入格式(JSON): {\"city\": \"城市名\", \"days\": 天数, \"preferences\": \"偏好\", \"start_date\": \"YYYY-MM-DD\"}\n"
        "preferences可选值: 自然风光, 美食, 历史文化, 购物, 亲子, 休闲, 综合\n"
        "start_date可选, 不提供则默认为近期"
    )

    def _run(self, query: str) -> str:
        try:
            params = json.loads(query)
        except json.JSONDecodeError:
            return "输入格式错误，请提供JSON格式: {\"city\": \"城市名\", \"days\": 天数, \"preferences\": \"偏好\"}"

        city = params.get("city", "")
        days = params.get("days", 3)
        preferences = params.get("preferences", "综合")
        start_date = params.get("start_date", "")

        if not city:
            return "请提供目的地城市名称"

        amap = get_amap()

        # 1. Get weather for the destination
        weather_info = ""
        try:
            wdata = amap.get_weather(city, extensions="all")
            if "forecasts" in wdata:
                fc = wdata["forecasts"][0]
                weather_lines = [f"【{city}天气预报】"]
                for cast in fc["casts"][:days]:
                    weather_lines.append(
                        f"{cast['date']}: {cast['dayweather']} {cast['daytemp']}°C / "
                        f"夜间{cast['nightweather']} {cast['nighttemp']}°C"
                    )
                weather_info = "\n".join(weather_lines)
        except Exception as e:
            weather_info = f"天气查询失败: {e}"

        # 2. Search POIs for attractions and food
        attractions = []
        restaurants = []
        try:
            poi_att = amap.search_poi("景点", city, offset=10)
            for poi in poi_att.get("pois", []):
                attractions.append({
                    "name": poi["name"],
                    "address": poi.get("address", ""),
                    "location": poi.get("location", ""),
                    "type": poi.get("type", ""),
                })

            food_keyword = _get_food_keyword(preferences)
            poi_food = amap.search_poi(food_keyword, city, offset=10)
            for poi in poi_food.get("pois", []):
                restaurants.append({
                    "name": poi["name"],
                    "address": poi.get("address", ""),
                    "location": poi.get("location", ""),
                    "type": poi.get("type", ""),
                })
        except Exception as e:
            attractions = []
            restaurants = []

        # 3. Use LLM to generate itinerary
        llm = ChatTongyi(
            model=settings.llm_model,
            dashscope_api_key=settings.dashscope_api_key,
            temperature=0.7,
        )

        prompt = _build_itinerary_prompt(
            city=city,
            days=days,
            preferences=preferences,
            start_date=start_date,
            weather_info=weather_info,
            attractions=attractions,
            restaurants=restaurants,
        )

        try:
            response = llm.invoke(prompt)
            itinerary = response.content
        except Exception as e:
            itinerary = f"行程生成失败: {e}"

        # 4. Build result
        result_parts = [itinerary]
        if weather_info:
            result_parts.insert(0, weather_info)

        return "\n\n".join(result_parts)

    async def _arun(self, query: str) -> str:
        return self._run(query)


def _get_food_keyword(preferences: str) -> str:
    mapping = {
        "美食": "美食|特色餐厅",
        "自然风光": "当地小吃|农家菜",
        "历史文化": "老字号|传统美食",
        "购物": "美食广场|商场餐厅",
        "亲子": "亲子餐厅|家庭餐",
        "休闲": "咖啡|茶馆|轻食",
    }
    return mapping.get(preferences, "美食|特色餐厅")


def _build_itinerary_prompt(
    city: str,
    days: int,
    preferences: str,
    start_date: str,
    weather_info: str,
    attractions: list,
    restaurants: list,
) -> str:
    attr_str = "\n".join(
        [f"- {a['name']} ({a.get('address', '')})" for a in attractions[:8]]
    ) if attractions else "(POI数据暂缺)"
    food_str = "\n".join(
        [f"- {r['name']} ({r.get('address', '')})" for r in restaurants[:8]]
    ) if restaurants else "(美食数据暂缺)"

    date_hint = f"出发日期为{start_date}" if start_date else "出发日期为近期"

    return f"""你是一个专业的旅行规划师。请根据以下信息为{days}天的{city}行程生成详细计划。

【用户偏好】
{preferences}

【日期】
{date_hint}，共{days}天

【天气信息】
{weather_info}

【可用景点】
{attr_str}

【可用餐厅/美食】
{food_str}

【输出要求】
为每天生成结构化的行程，每天分 上午/下午/晚上 三个时段。
每个时段列出 1-2 个具体地点或活动，以及简单的说明。
行程最后附上独立的"注意事项"部分，包含：
- 天气提醒与穿着建议
- 交通建议
- 饮食注意事项
- 安全提示

请以清晰的 markdown 格式输出，天标题用 ## 第X天。"""
