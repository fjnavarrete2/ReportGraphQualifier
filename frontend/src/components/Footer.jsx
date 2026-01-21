import './Footer.css';
import { useApp } from '../AppContext'; // Importamos el contexto

export default function Footer() {
  const { t } = useApp(); // Extraemos la función de traducción

  return (
    <footer className="footer">
      <p>{t('footer.copyright')}</p>
    </footer>
  );
}