import './Navbar.css';
import logo from '../assets/logo.png';
import { NavLink, Link } from 'react-router-dom';
import { useState } from 'react';
import { FiMenu, FiX } from 'react-icons/fi';
import { useApp } from '../AppContext';

export default function Navbar() {
  const { language, toggleLanguage, t } = useApp();
  const [open, setOpen] = useState(false);
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-left" style={{ textDecoration: 'none', color: 'inherit' }}>
          <img src={logo} alt="Logo" className="navbar-logo" />
          <h2 className="navbar-title">OntoPropertyCrime</h2>
        </Link>
        <button className="navbar-toggle" onClick={() => setOpen(!open)}>
          {open ? <FiX /> : <FiMenu />}
        </button>
        <ul className={`navbar-menu ${open ? 'open' : ''}`}>
          <li>
            <NavLink
              to="/atestados"
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
             {t('navbar.process')}
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/analizador"
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
             {t('navbar.visualize')}
            </NavLink>
          </li>
          <li>
            <button onClick={toggleLanguage} className="lang-selector">
              {language === 'es' ? '🇪🇸 ES' : '🇬🇧 EN'}
            </button>
          </li>
        </ul>
      </div>
    </nav>
  );
}
