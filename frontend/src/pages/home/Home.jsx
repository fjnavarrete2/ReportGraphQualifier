import fondo from '../../assets/fondo.jpg';
import './Home.css';
import { Link } from 'react-router-dom';
import { useApp } from '../../AppContext'; // Importamos el hook para usar t

export default function Home() {
  const { t } = useApp(); // Extraemos la función de traducción

  return (
    <div className="home" style={{ backgroundImage: `url(${fondo})` }}>
      <div className="overlay">
        <div className="home-content">
          {/* Título dinámico */}
          <h1>{t('home.title')}</h1>
          
          {/* Descripción dinámica */}
          <p>
            {t('home.description')}
          </p>
          
          <div className="home-buttons">
            {/* Botón Procesamiento */}
            <Link to="/atestados" className="home-btn">
              {t('home.btn_process')}
            </Link>
            
            {/* Botón Visualización */}
            <Link to="/analizador" className="home-btn">
              {t('home.btn_visualize')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
