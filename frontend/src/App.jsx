// frontend/src/App.jsx
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/home/Home';
import Analizador from './pages/analizador/Analizador';
import Atestados from './pages/atestados/Atestados';
import Neo4j from './pages/neo4j/Neo4j';
import VisorHTML from './pages/analizador/VisorHTML';
import ResumenGrafo from './pages/analizador/ResumenGrafo';
import ResumenResultado from './pages/analizador/ResultadoGrafo';
import { Routes, Route } from 'react-router-dom';
import './App.css';
import { AppProvider } from './AppContext';

function App() {
  return (
    <AppProvider>
      <div className="app-wrapper">
        <a href="#main" className="skip-link">Saltar al contenido</a>
        <Navbar />
        <main id="main" className="main-hero">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/atestados" element={<Atestados />} />
            <Route path='/analizador' element={<Analizador />} />
            <Route path="/neo4j" element={<Neo4j />} />
            <Route path="/analizador/visor" element={<VisorHTML />} /> 
            <Route path="/analizador/resumen" element={<ResumenGrafo />} />
            <Route path="/analizador/resultado" element={<ResumenResultado />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </AppProvider>
  );
}

export default App;
