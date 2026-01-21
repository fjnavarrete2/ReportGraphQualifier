import './Analizador.css'; 
import { useRef, useState } from 'react';
import axios from 'axios';
import { FiUpload, FiDatabase, FiPlay, FiAlertCircle } from 'react-icons/fi';

export default function Neo4j() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [rootName, setRootName] = useState("Atestado");
  const [articles, setArticles] = useState(""); 
  
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) setFile(selectedFile);
  };

  const ejecutarImportacion = async () => {
    if (!file) return alert("Por favor, selecciona primero un archivo .ttl");
    setLoading(true);
    setStatus(null);
    
    try {
      const payload = {
        file_path: file.name, 
        root_name: rootName,
        articles: articles.split(',').map(a => a.trim()).filter(a => a !== "")
      };

      const response = await axios.post('http://localhost:8000/cargaNeo4j', payload);
      setStatus({ type: 'success', msg: 'Importación completada con éxito' });
    } catch (err) {
      console.error(err);
      setStatus({ type: 'error', msg: 'Error: No se pudo conectar con Neo4j' });
    } finally {
      setLoading(false);
    }
  };

  return (
    /* CAMBIO: de analizador-container a analizador-wrapper */
    <div className="analizador-wrapper"> 
      <h1>Carga de Grafo en Neo4j</h1>
      
      {/* CAMBIO: de toolbar a analizador-formulario */}
      <div className="analizador-formulario">
        <input
          type="file"
          accept=".ttl,.rdf,.owl"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        
        <button className="btn archivo-btn" onClick={() => fileInputRef.current.click()}>
          <FiUpload style={{ marginRight: '6px' }} />
          Seleccionar TTL
        </button>

        <button 
          className="btn analizar-btn" 
          onClick={ejecutarImportacion}
          disabled={!file || loading}
        >
          {loading ? "Procesando..." : <><FiPlay style={{ marginRight: '6px' }} /> Importar a BD</>}
        </button>
      </div>

      <div className="config-panel-neo4j">
        <input 
          type="text" 
          value={rootName} 
          onChange={(e) => setRootName(e.target.value)}
          placeholder="Nodo Raíz"
          className="input-config"
        />
        <input 
          type="text" 
          value={articles} 
          onChange={(e) => setArticles(e.target.value)}
          placeholder="Artículos (Separados por coma)"
          className="input-config"
        />
      </div>

      <div className="visualizacion">
        {status ? (
          <div className={`resultado ${status.type}`}>
            {status.type === 'success' ? <FiDatabase size={40} color="green" /> : <FiAlertCircle size={40} color="red" />}
            <h2>{status.msg}</h2>
          </div>
        ) : (
          <p className="grafotip">
            {file ? `Listo: ${file.name}` : "Seleccione un archivo para comenzar."}
          </p>
        )}
      </div>
    </div>
  );
}