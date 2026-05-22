import React from 'react';
import SEO from './SEO';
import WeatherWidget from './WeatherWidget';

const Home: React.FC = () => {
  return (
    <>
      <SEO
        title="Laundry Scheduler - Главная | Бронирование стиральных машин"
        description="Онлайн система бронирования стиральных машин и сушилок. Удобное расписание, управление бронированиями в реальном времени."
        canonical="https://laundry-scheduler.local/"
      />
      
      <div className="home-page">
        <h1>Добро пожаловать в систему бронирования стиральных машин!</h1>
        <p>На этой платформе вы можете забронировать стиральную машину или сушилку на определенное время.</p>

        <WeatherWidget />

        <div className="features">
          <div className="feature-card">
            <h3>📅 Бронирование</h3>
            <p>Выберите удобное время для стирки</p>
          </div>
          <div className="feature-card">
            <h3>⏰ График</h3>
            <p>Просматривайте расписание бронирований</p>
          </div>
          <div className="feature-card">
            <h3>👥 Управление</h3>
            <p>Управляйте своими бронированиями</p>
          </div>
        </div>
      </div>
    </>
  );
};

export default Home;
