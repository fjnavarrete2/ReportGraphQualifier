import { createContext, useState, useContext } from 'react';
import translations from './translations.json'; // Importa el JSON anterior

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [file, setFile] = useState(null);
  const [debugJson, setDebugJson] = useState(null); // Para mostrar el JSON
  const [language, setLanguage] = useState('es'); // 'es' o 'en'
  const [actionStatus, setActionStatus] = useState({
    referencias: { status: 'esperando', msg: '-' },
    resumen: { status: 'esperando', msg: '-' },
    resultado: { status: 'esperando', msg: '-' }
  });

  // Función de traducción
  const t = (path) => {
    const keys = path.split('.');
    let result = translations[language];
    keys.forEach(key => {
        result = result ? result[key] : path;
    });
    return result || path;
  };

  const toggleLanguage = () => setLanguage(prev => prev === 'es' ? 'en' : 'es');

  return (
    <AppContext.Provider value={{ 
      language, setLanguage, t, toggleLanguage,
      file, setFile, actionStatus, setActionStatus,debugJson, setDebugJson 
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);