import './Atestados.css';
import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { FiUpload, FiTrash2, FiDownload, FiLoader, FiSearch, FiDatabase, FiShare2 } from 'react-icons/fi';
import docs from '../../assets/docs.png';
import noArchivo from '../../assets/noArchivo.png';
// O si instalas lucide-react (muy recomendado para grafos):
// import { LuTreeGraph } from "react-icons/lu";
import { useApp } from '../../AppContext';

export default function Atestados() {
  const [file, setFile] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [popup, setPopup] = useState(false);
  const [error, setError] = useState(null);
  const overlayRef = useRef(null);
  const fileInputRef = useRef(null);
  const [inferring, setInferring] = useState(false); // Nuevo estado para la inferencia
  const { t } = useApp();

  // Dentro de Atestados()
const [importing, setImporting] = useState(false);
const [importSuccess, setImportSuccess] = useState(null); // Almacenará el mensaje detallado
const [ttlBlob, setTtlBlob] = useState(null);

// Estado para controlar el historial de acciones
// const [actionHistory, setActionHistory] = useState({
//   procesar: { status: 'esperando', msg: '-' },
//   descargar: { status: 'esperando', msg: '-' },
//   inferir: { status: 'esperando', msg: '-' },
//   neo4j: { status: 'esperando', msg: '-' }
// });
const [actionHistory, setActionHistory] = useState({
    procesar: { status: 'esperando', msg: t('atestados.messages.waiting') },
    inferir: { status: 'esperando', msg: t('atestados.messages.waiting') },
    descargar: { status: 'esperando', msg: t('atestados.messages.waiting') },
    neo4j: { status: 'esperando', msg: t('atestados.messages.waiting') }
  });

// Estado para almacenar los JSON específicos que queremos mostrar
const [debugJson, setDebugJson] = useState(null);
// const StatusBadge = ({ status }) => {
//   switch (status) {
//     case 'ok': return <span style={{ color: '#28a745' }}>● Satisfactorio</span>;
//     case 'error': return <span style={{ color: '#dc3545' }}>● Error</span>;
//     default: return <span style={{ color: '#6c757d' }}>○ Pendiente</span>;
//   }
// };
const StatusBadge = ({ status }) => {
  const { t } = useApp();
  const styles = {
    ok: { color: '#28a745', fontWeight: 'bold' },
    error: { color: '#dc3545', fontWeight: 'bold' },
    esperando: { color: '#6c757d' }
  };
  // Mapeamos los estados a las llaves del JSON
  const labelKey = status === 'ok' ? 'common.status.ok' : 
                   status === 'error' ? 'common.status.error' : 
                   'common.status.waiting';

  return <span style={styles[status] || styles.esperando}>{t(labelKey)}</span>;
};

const ARTICULOS_DEFAULT = [
  "Article240_1", "Article242_1", "Article234_1", "Article234_2", 
  "Article234_3", "Article235_1", "Article235_2", "Article236_1", 
  "Article236_2", "Article240_2", "Article241_1", "Article241_4", 
  "Article242_2", "Article242_3", "Article242_4"
];

  // Manejo de accesibilidad para el popup de carga
  useEffect(() => {
    if (!popup) return;
    const overlay = overlayRef.current;
    if (overlay) overlay.focus();

    const handleKey = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        setPopup(false);
      }
    };

    overlay?.addEventListener('keydown', handleKey);
    return () => overlay?.removeEventListener('keydown', handleKey);
  }, [popup]);

  const handleChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setResultado(null); // Limpiar resultado previo al cambiar archivo
      setTtlBlob(null);
      setDebugJson(null);
      setActionHistory({
        procesar: { status: 'esperando', msg: '-' },
        descargar: { status: 'esperando', msg: '-' },
        inferir: { status: 'esperando', msg: '-' },
        neo4j: { status: 'esperando', msg: '-' }
      });
      setError(null);
    }
  };

  const handleDelete = () => {
    setFile(null);
    setResultado(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setPopup(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // const res = await axios.post("http://localhost:8000/procesarG/", formData);
      const response = await axios.post('http://localhost:8000/procesarG/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResultado(response.data);
      setActionHistory(prev => ({ ...prev, procesar: { status: 'ok', msg: t('atestados.messages.success') }}));
      setDebugJson(response.data); // Guardamos para mostrar abajo
    } catch (err) {
      console.error(err);
      // setError("Error al procesar el documento. Inténtalo de nuevo.");
      setActionHistory(prev => ({ ...prev, procesar: { status: 'error', msg: err.message }}));
    } finally {
      setLoading(false);
      setPopup(false);
    }
  };

  const descargarRDF = async () => {
    try {
      const response = await axios.post("http://localhost:8000/generar_rdfG/", resultado, {
        responseType: 'blob'   
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', resultado.nombre_grafo + '.rdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      setActionHistory(prev => ({ ...prev, descargar: { status: 'ok', msg: t('atestados.messages.success') }}));
      setDebugJson(null); // Limpiamos el JSON según tu instrucción
    } catch (err) {
      console.error("Error al descargar el RDF:", err);
      setActionHistory(prev => ({ ...prev, descargar: { status: 'error', msg: t('atestados.messages.error') }}));
      // alert("No se pudo descargar el archivo RDF.");
    }
  };

  const handleInferencia = async () => {
    if (!resultado) return;
    setInferring(true);
    setError(null);

    try {
        // 1. Petición con responseType blob
        const response = await axios.post("http://localhost:8000/inferir_grafo_ttls/", resultado, {
        responseType: 'blob'   
        });

        // 2. Guardar en el estado de React
        const blob = new Blob([response.data], { type: 'text/turtle' });
        setTtlBlob(blob);

        // 3. Descarga automática para el usuario
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', resultado.nombre_grafo + '.ttls');
        document.body.appendChild(link);
        link.click();
        link.remove();
        setActionHistory(prev => ({ ...prev, inferir: { status: 'ok', msg: t('atestados.messages.success') }}));
        setDebugJson(null); // Limpiamos el JSON según tu instrucción
        
        // Si el WS devuelve un nuevo JSON o confirmación, lo actualizamos
        // Opcional: setResultado(response.data); 
        // alert("Inferencia completada con éxito.");
    } catch (err) {
        console.error("Error en la inferencia:", err);
        setActionHistory(prev => ({ ...prev, inferir: { status: 'error', msg: t('atestados.messages.error') }}));
        // alert("No se pudo descargar el archivo TTL.");
    } finally {
        setInferring(false);
    }

  
};

  const handleImportNeo4j = async () => {
  if (!ttlBlob) return;
  setImporting(true);
  setImportSuccess(null);
  try {
    // Transformamos el Blob guardado en memoria a un objeto "File" (similar a UploadFile)
    const fileToUpload = new File([ttlBlob], "grafo_importar.ttl", { type: "text/turtle" });
    
    const formData = new FormData();
    const file_name = file.name.split('.').slice(0, -1).join('.')

    formData.append('file', fileToUpload);
    formData.append('root_name', file_name);
    formData.append('articles', JSON.stringify(ARTICULOS_DEFAULT));
    formData.append('llm_type', "ttls");

    const response = await axios.post('http://localhost:8000/cargaNeo4j/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

    console.log(response.data)
    if (response.data.status === "success") {
      // setImportSuccess(`Éxito: Se han importado ${ARTICULOS_DEFAULT.length} artículos.`);
      setActionHistory(prev => ({ ...prev, neo4j: { status: 'ok', msg: response.data.mensaje }}));
      setDebugJson(response.data); // Guardamos para mostrar abajo
    }
   else{
      setActionHistory(prev => ({ ...prev, neo4j: { status: 'error', msg: response.data.mensaje }}));
   }
  } catch (err) {
    setActionHistory(prev => ({ ...prev, neo4j: { status: 'error', msg: response.data.mensaje }}));
    // setError("Error en Neo4j: " + (err.response?.data?.detail || err.message));
  } finally {
    setImporting(false);
  }
};

  

  return (
    <div className="atestados-wrapper">
      <h1>{t('atestados.principalTitle')}</h1>
      <p className="subtitulo">{t('atestados.subtitle')}</p>

      {/* Indicador visual de pasos */}
      <div className="pasos">
        <div className="paso"><span>1</span> {t('atestados.steps.step1')}</div>
        <div className="paso"><span>2</span> {t('atestados.steps.step2')}</div>
        <div className="paso"><span>3</span> {t('atestados.steps.step3')}</div>
        <div className="paso"><span>4</span> {t('atestados.steps.step4')}</div>
        <div className="paso"><span>5</span> {t('atestados.steps.step5')}</div>
      </div>

      {/* CONTENEDOR DE BOTONES ALINEADOS HORIZONTALMENTE */}
      <div className="acciones-atestados">
        <input
          type="file"
          accept=".pdf,.docx"
          ref={fileInputRef}
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        
        {/* BOTÓN 1: SELECCIONAR */}
        <button 
          className="btn archivo-btn" 
          onClick={() => fileInputRef.current.click()}
          aria-label= {t('atestados.btns.select')}
        >
          <FiUpload style={{ marginRight: '8px' }} />
          {t('atestados.btns.select')}
        </button>

        {/* BOTÓN 2: PROCESAR */}
        <button 
          className="btn procesar-btn" 
          onClick={handleUpload} 
          disabled={!file || loading}
          aria-label={t('atestados.btns.process')}
        >
          {loading ? <FiLoader className="spinner-mini" /> : <FiSearch style={{ marginRight: '8px' }} />}
          {t('atestados.btns.process')}
        </button>

        {/* BOTÓN 3: DESCARGAR */}
        <button 
          className="btn descargar-btn" 
          onClick={descargarRDF} 
          disabled={!resultado || loading}
          aria-label={t('atestados.btns.download')}
        >
          <FiDownload style={{ marginRight: '8px' }} />
          {t('atestados.btns.download')}
        </button>

        {/* BOTÓN 4: INFERIR (NUEVO) */}
        <button 
          className="btn inferir-btn" 
          onClick={handleInferencia} 
          disabled={!resultado || loading}
        >
          {inferring ? <FiLoader className="spinner-mini" /> : <FiShare2 style={{ marginRight: '8px' }} />}
          {t('atestados.btns.infer')}
        </button>

        {/* BOTÓN 5: IMPORTAR A NEO4J */}
        <button 
          className="btn importar-btn" 
          onClick={handleImportNeo4j} 
          disabled={!ttlBlob || loading}
        >
          {importing ? <FiLoader className="spinner-mini-import" /> : <FiDatabase style={{ marginRight: '8px' }} />}
          {t('atestados.btns.import')}
        </button>
      </div>

      <div className="procesamiento-grid">
        {/* Lado Izquierdo: Vista previa del archivo */}
        <div className="archivo-container">
          <div className="preview-card">
            <img src={file ? docs : noArchivo} alt="Vista previa" />
            <p className="file-name">{file ? file.name : t('atestados.preview.no_file')}</p>
            {file && (
              <button className="delete-btn" onClick={handleDelete} title="Eliminar archivo">
                <FiTrash2 />
              </button>
            )}
          </div>
        </div>

        
        <div className="resultado-container">
          <div className="resultado-card">
            <h3>Panel de Control de Procesos</h3>
            
            <table className="status-table">
              <thead>
                <tr>
                  <th>{t('atestados.panel.col_action')}</th>
                  <th>{t('atestados.panel.col_status')}</th>
                  <th>{t('atestados.panel.col_detail')}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>{t('atestados.panel.actions.process')}</strong></td>
                  <td><StatusBadge status={actionHistory.procesar.status} /></td>
                  <td>{actionHistory.procesar.msg}</td>
                </tr>
                <tr>
                  <td><strong>{t('atestados.panel.actions.download')}</strong></td>
                  <td><StatusBadge status={actionHistory.descargar.status} /></td>
                  <td>{actionHistory.descargar.msg}</td>
                </tr>
                <tr>
                  <td><strong>{t('atestados.panel.actions.infer')}</strong></td>
                  <td><StatusBadge status={actionHistory.inferir.status} /></td>
                  <td>{actionHistory.inferir.msg}</td>
                </tr>
                <tr>
                  <td><strong>{t('atestados.panel.actions.import')}</strong></td>
                  <td><StatusBadge status={actionHistory.neo4j.status} /></td>
                  <td>{actionHistory.neo4j.msg}</td>
                </tr>
              </tbody>
            </table>

            {/* Sección de detalles JSON filtrada */}
            <details className="json-details" style={{ marginTop: '20px' }}>
              <summary>{t('atestados.debug.title')}</summary>
              <div className="json-viewer">
                {debugJson ? (
                  <pre>{JSON.stringify(debugJson, null, 2)}</pre>
                ) : (
                  <p className="placeholder-text">{t('atestados.debug.no_data')}</p>
                )}
              </div>
            </details>
          </div>
        </div>
      </div>

      {/* Overlay de carga */}
      {popup && (
        <div className="popup-overlay" ref={overlayRef} tabIndex="-1" role="dialog">
          <div className="popup-loader">
            <div className="spinner" />
            <p>{t('atestados.loading.title')}</p>
            <small>{t('atestados.loading.wait')}</small>
          </div>
        </div>
      )}
    </div>
  );
}