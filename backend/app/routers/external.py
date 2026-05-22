"""
Router для интеграции со сторонними API.
Предоставляет endpoint'ы для получения внешних данных.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.services.weather_service import get_weather_service, WeatherService

router = APIRouter(prefix="/external", tags=["external-apis"])


@router.get("/weather")
async def get_weather(
    lat: float = Query(..., description="Широта"),
    lon: float = Query(..., description="Долгота"),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Получение текущей погоды по координатам.
    
    Использует OpenWeatherMap API.
    Если API ключ не настроен, возвращает заглушку.
    """
    weather = await weather_service.get_weather(lat, lon)
    
    if weather is None:
        # Возвращаем заглушку если API недоступен
        return {
            "warning": "Weather API unavailable, using mock data",
            "mock_data": {
                "name": "Moscow",
                "main": {
                    "temp": 20,
                    "humidity": 50,
                    "pressure": 1013
                },
                "weather": [
                    {"description": "clear sky"}
                ],
                "wind": {
                    "speed": 5
                }
            }
        }
    
    return weather


@router.get("/weather/forecast")
async def get_weather_forecast(
    lat: float = Query(..., description="Широта"),
    lon: float = Query(..., description="Долгота"),
    days: int = Query(3, ge=1, le=5, description="Количество дней (1-5)"),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Получение прогноза погоды.
    """
    forecast = await weather_service.get_forecast(lat, lon, days)
    
    if forecast is None:
        return {
            "warning": "Weather forecast API unavailable",
            "mock_data": {
                "list": [
                    {
                        "dt": 1234567890,
                        "main": {"temp": 20},
                        "weather": [{"description": "clear sky"}]
                    }
                ]
            }
        }
    
    return forecast


@router.get("/weather/recommendation")
async def get_drying_recommendation(
    lat: float = Query(..., description="Широта"),
    lon: float = Query(..., description="Долгота"),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Получение рекомендации по сушке на основе погоды.
    
    Полезно для пользователей сушилок - помогает решить,
    можно ли сушить белье на улице.
    """
    recommendation = await weather_service.get_weather_recommendation(lat, lon)
    
    if recommendation is None:
        recommendation = "Не удалось получить рекомендацию. Используйте сушилку."
    
    return {
        "recommendation": recommendation,
        "location": {"lat": lat, "lon": lon}
    }