"""
Сервис для интеграции со сторонним API.
В качестве примера используется OpenWeatherMap API для получения погоды,
что может быть полезно для рекомендаций по использованию сушилки.
"""
import asyncio
import os
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime

# Конфигурация
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"


class WeatherService:
    """
    Сервис для работы с OpenWeatherMap API.
    Используется для получения данных о погоде.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENWEATHER_API_KEY
        self.base_url = OPENWEATHER_BASE_URL
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание HTTP сессии"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Закрытие сессии"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Получение текущей погоды по координатам.
        
        :param lat: Широта
        :param lon: Долгота
        :return: Данные о погоде или None при ошибке
        """
        if not self.api_key:
            return None
        
        try:
            session = await self._get_session()
            url = f"{self.base_url}/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
                "lang": "ru"
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    # Rate limit exceeded
                    return None
                else:
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None
    
    async def get_forecast(self, lat: float, lon: float, days: int = 5) -> Optional[Dict[str, Any]]:
        """
        Получение прогноза погоды.
        
        :param lat: Широта
        :param lon: Долгота
        :param days: Количество дней (максимум 5)
        :return: Прогноз погоды или None при ошибке
        """
        if not self.api_key:
            return None
        
        try:
            session = await self._get_session()
            url = f"{self.base_url}/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
                "lang": "ru",
                "cnt": days * 8  # 8 прогнозов в день
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None
    
    async def get_weather_recommendation(self, lat: float, lon: float) -> Optional[str]:
        """
        Получение рекомендации по использованию сушилки на основе погоды.
        
        :param lat: Широта
        :param lon: Долгота
        :return: Текстовая рекомендация
        """
        weather = await self.get_weather(lat, lon)
        
        if not weather:
            return "Не удалось получить данные о погоде. Рекомендуется использовать сушилку."
        
        temp = weather.get("main", {}).get("temp", 20)
        humidity = weather.get("main", {}).get("humidity", 50)
        description = weather.get("weather", [{}])[0].get("description", "")
        
        # Логика рекомендаций
        if temp > 25 and humidity < 40 and "дожд" not in description.lower():
            return "Отличная погода для сушки на улице! 🌞"
        elif temp > 15 and humidity < 60 and "дожд" not in description.lower():
            return "Хорошая погода, можно сушить на улице. ☀️"
        elif "дожд" in description.lower() or "снег" in description.lower():
            return "Плохая погода, рекомендуется использовать сушилку. 🌧️"
        elif humidity > 70:
            return "Высокая влажность, лучше использовать сушилку. 💧"
        else:
            return "Погода нейтральная, можно использовать любой способ сушки. ⛅"
        
        return "Рекомендуется использовать сушилку."


# Singleton instance
_weather_service: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    """Получение экземпляра сервиса погоды (singleton)"""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service
