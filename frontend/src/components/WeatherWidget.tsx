import React, { useState, useEffect } from 'react';
import { externalAPI } from '../services/api';
import './WeatherWidget.css';

interface WeatherMain {
  temp: number;
  humidity: number;
  pressure: number;
}

interface WeatherData {
  name?: string;
  main?: WeatherMain;
  weather?: { description: string }[];
  wind?: { speed: number };
  warning?: string;
  mock_data?: {
    name?: string;
    main?: WeatherMain;
    weather?: { description: string }[];
    wind?: { speed: number };
  };
}

const DEFAULT_LAT = 55.7558;
const DEFAULT_LON = 37.6173;

const WeatherWidget: React.FC = () => {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [recommendation, setRecommendation] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [coords, setCoords] = useState({ lat: DEFAULT_LAT, lon: DEFAULT_LON });

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        () => {}
      );
    }
  }, []);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [weatherRes, recRes] = await Promise.all([
          externalAPI.getWeather(coords.lat, coords.lon),
          externalAPI.getRecommendation(coords.lat, coords.lon),
        ]);
        setWeather(weatherRes.data);
        setRecommendation(recRes.data.recommendation);
      } catch {
        setRecommendation('Не удалось загрузить данные о погоде.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [coords]);

  const data = weather?.mock_data ?? weather;
  const temp = data?.main?.temp;
  const humidity = data?.main?.humidity;
  const description = data?.weather?.[0]?.description;
  const city = data?.name;
  const isMock = !!weather?.warning;

  return (
    <div className="weather-widget">
      <h3 className="weather-title">
        Погода{city ? ` — ${city}` : ''}
      </h3>

      {loading ? (
        <p className="weather-loading">Загрузка...</p>
      ) : (
        <>
          {isMock && (
            <p className="weather-mock-notice">Демо-данные (API ключ не настроен)</p>
          )}
          {temp !== undefined && (
            <div className="weather-info">
              <span className="weather-temp">{Math.round(temp)}°C</span>
              <div className="weather-details">
                {description && <span className="weather-desc">{description}</span>}
                {humidity !== undefined && (
                  <span className="weather-humidity">Влажность: {humidity}%</span>
                )}
              </div>
            </div>
          )}
          <div className="weather-recommendation">
            {recommendation}
          </div>
        </>
      )}
    </div>
  );
};

export default WeatherWidget;
