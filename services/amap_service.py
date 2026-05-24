import httpx
from typing import Optional
from backend.config import get_settings

settings = get_settings()


class AmapService:
    """Amap (高德地图) Web Service API wrapper."""

    def __init__(self):
        self.base_url = settings.amap_base_url
        self.api_key = settings.amap_api_key
        self.client = httpx.Client(timeout=15.0)

    def _get(self, path: str, params: dict) -> dict:
        params["key"] = self.api_key
        resp = self.client.get(f"{self.base_url}{path}", params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "1":
            raise Exception(f"Amap API error: {data.get('info', 'unknown')}")
        return data

    def get_weather(self, city: str, extensions: str = "base") -> dict:
        """Query weather for a city.

        Args:
            city: City name or adcode
            extensions: "base" for live weather, "all" for forecast
        """
        return self._get("/weather/weatherInfo", {
            "city": city,
            "extensions": extensions,
        })

    def get_weather_by_adcode(self, adcode: str, extensions: str = "base") -> dict:
        return self.get_weather(adcode, extensions)

    def search_poi(self, keywords: str, city: str = "", offset: int = 10, page: int = 1) -> dict:
        """Search POI (points of interest).

        Args:
            keywords: Search keywords (e.g. "景点", "酒店", "美食")
            city: City name or adcode to limit search scope
            offset: Number of results per page
        """
        params = {"keywords": keywords, "offset": offset, "page": page}
        if city:
            params["city"] = city
        return self._get("/place/text", params)

    def search_poi_around(self, location: str, keywords: str, radius: int = 3000, offset: int = 10) -> dict:
        """Search POI around a location.

        Args:
            location: "lng,lat" format
            keywords: Search keywords
            radius: Search radius in meters
        """
        return self._get("/place/around", {
            "location": location,
            "keywords": keywords,
            "radius": radius,
            "offset": offset,
        })

    def get_district(self, keywords: str, subdistrict: int = 1) -> dict:
        """Get administrative district info including adcode.

        Args:
            keywords: City or district name
            subdistrict: Level of sub-district data (0-3)
        """
        return self._get("/config/district", {
            "keywords": keywords,
            "subdistrict": subdistrict,
        })

    def geo_code(self, address: str, city: str = "") -> dict:
        """Convert address to coordinates.

        Args:
            address: Address string
            city: City scope hint
        """
        params = {"address": address}
        if city:
            params["city"] = city
        return self._get("/geocode/geo", params)

    def ip_location(self, ip: str) -> dict:
        """IP location lookup."""
        return self._get("/ip", {"ip": ip})

    def close(self):
        self.client.close()


_amap_instance: Optional[AmapService] = None


def get_amap() -> AmapService:
    global _amap_instance
    if _amap_instance is None:
        _amap_instance = AmapService()
    return _amap_instance
