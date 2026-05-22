import React from 'react';
import './Spinner.css';

const Spinner: React.FC = () => {
  return (
    <div className="spinner-container">
      <div className="spinner"></div>
      <p>Загрузка...</p>
    </div>
  );
};

export default Spinner;
