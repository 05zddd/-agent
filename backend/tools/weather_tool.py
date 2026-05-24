from langchain.tools import BaseTool
from services.amap_service import get_amap


class WeatherTool(BaseTool):
    name: str = "weather_query"
    description: str = (
        "查询指定城市的天气信息。输入格式: 城市名,查询类型\n"
        "查询类型: base=实时天气(默认), all=天气预报(未来3-4天)\n"
        "示例输入: 北京,base  或  上海,all"
    )

    def _run(self, query: str) -> str:
        parts = query.strip().split(",")
        city = parts[0].strip()
        extensions = parts[1].strip() if len(parts) > 1 else "base"

        if extensions not in ("base", "all"):
            extensions = "base"

        amap = get_amap()

        try:
            data = amap.get_weather(city, extensions=extensions)

            if extensions == "base" and "lives" in data:
                live = data["lives"][0]
                return (
                    f"【{live['city']} 实时天气】\n"
                    f"天气: {live['weather']}\n"
                    f"温度: {live['temperature']}°C\n"
                    f"风向: {live['winddirection']} {live['windpower']}级\n"
                    f"湿度: {live['humidity']}%\n"
                    f"发布时间: {live['reporttime']}"
                )

            if extensions == "all" and "forecasts" in data:
                fc = data["forecasts"][0]
                lines = [f"【{fc['city']} 天气】", f"发布时间: {fc['reporttime']}", ""]
                for cast in fc["casts"]:
                    lines.append(
                        f"📅 {cast['date']} ({_weekday_str(cast.get('week', ''))})\n"
                        f"   白天: {cast['dayweather']} {cast['daytemp']}°C {cast['daywind']}{cast['daypower']}级\n"
                        f"   夜间: {cast['nightweather']} {cast['nighttemp']}°C {cast['nightwind']}{cast['nightpower']}级"
                    )
                return "\n".join(lines)

            return f"天气查询结果: {data}"

        except Exception as e:
            return f"天气查询失败: {str(e)}"

    async def _arun(self, query: str) -> str:
        return self._run(query)


def _weekday_str(w: str) -> str:
    mapping = {"1": "周一", "2": "周二", "3": "周三", "4": "周四", "5": "周五", "6": "周六", "7": "周日"}
    return mapping.get(w, w)
