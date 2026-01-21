import { useEffect, useState } from "react";
import { useApp } from "../../AppContext";

export default function VisorHTML() {
  const [html, setHtml] = useState("");
  const { t } = useApp();
  const [titulo, setTitulo] = useState(t("analizador.viewer"));

  useEffect(() => {
    // Intentamos recuperar el contenido de cualquiera de las dos funciones
    const content =
      sessionStorage.getItem("html_visor_contenido") ||
      sessionStorage.getItem("html_referencias");
    const customTitle = sessionStorage.getItem("visor_titulo");

    if (content) setHtml(content);
    if (customTitle) setTitulo(customTitle);
  }, []);

  if (!html) return <div className="loading-visor">Cargando contenido...</div>;

  return (
    <div
      className="visor-container"
      style={{ padding: "20px", height: "85vh" }}
    >
      {/* <h2 style={{ textAlign: 'center', color: '#1976d2', marginBottom: '15px' }}>{titulo}</h2> */}
      <iframe
        srcDoc={html}
        title={titulo}
        style={{
          width: "100%",
          height: "100%",
          border: "1px solid #ddd",
          borderRadius: "12px",
          boxShadow: "0 8px 20px rgba(0,0,0,0.15)",
        }}
      />
    </div>
  );
}
