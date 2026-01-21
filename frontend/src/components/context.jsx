import { createContext, useState } from 'react';

export const ResultadoContext = createContext();

export const ResultadoProvider = ({ children }) => {
  const [resultado, setResultado] = useState(null);

  return (
    <ResultadoContext.Provider value={{ resultado, setResultado }}>
      {children}
    </ResultadoContext.Provider>
  );
};
