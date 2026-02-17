import { useEffect, useState, useRef } from "react";
import { useApp } from "../../AppContext";
import tippy from 'tippy.js'; // Importamos la función core
import 'tippy.js/dist/tippy.css'; 
import 'tippy.js/themes/light-border.css'; // Asegúrate de tener este tema
import './Visor.css';

export default function VisorHTML() {
  const [html, setHtml] = useState("");
  const { t } = useApp();
  const [titulo, setTitulo] = useState(t("analizador.viewer"));
  const iframeRef = useRef(null); // Referencia para acceder al interior del iframe

  useEffect(() => {
    const content =
      sessionStorage.getItem("html_visor_contenido") ||
      sessionStorage.getItem("html_referencias");
    const customTitle = sessionStorage.getItem("visor_titulo");

    if (content) setHtml(content);
    if (customTitle) setTitulo(customTitle);
  }, []);

  // Esta función se ejecuta cuando el contenido del iframe termina de cargar
  // const handleIframeLoad = () => {
  //   if (iframeRef.current && iframeRef.current.contentDocument) {
  //     const doc = iframeRef.current.contentDocument;
  //     tippy(doc.querySelectorAll('.badge, strong[title]'), {
  //       content(reference) {
  //         const title = reference.getAttribute('title');
  //         if (!title) return '';

  //         const parts = title.split(' ');
  //         if (parts.length >= 3) {
  //           const sujeto = parts[0];
  //           const propiedad = parts[1];
  //           const objeto = parts.slice(2).join(' ');

  //           // Estructura en 3 renglones con la propiedad resaltada
  //           return `
  //             <div style="text-align: center; line-height: 1.4;">
  //               <div style="opacity: 0.8; font-size: 0.7rem;">${sujeto}</div>
  //               <div style="font-weight: 800; color: #ffd700; margin: 2px 0; text-transform: uppercase; letter-spacing: 0.5px;">
  //                 ${propiedad}
  //               </div>
  //               <div style="opacity: 0.8; font-size: 0.7rem;">${objeto}</div>
  //             </div>
  //           `;
  //         }
  //         return title;
  //       },
  //       allowHTML: true,
  //       theme: 'vibrant-dark', // Usaremos este nombre en el CSS
  //       animation: 'shift-away',
  //       appendTo: doc.body,
  //     });
  //   }
  // };

  const handleIframeLoad = () => {
    if (iframeRef.current && iframeRef.current.contentDocument) {
      const doc = iframeRef.current.contentDocument;

      // INYECTAR CSS DE TIPPY DENTRO DEL IFRAME
      const styleTag = doc.createElement("style");
      styleTag.innerHTML = `
        .tippy-box[data-theme~='custom-opaque'] {
          background-color: #1a1a1b !important;
          color: white !important;
          border: 1px solid #333 !important;
          border-radius: 6px !important;
          font-family: sans-serif;
        }
        /* Añade aquí el resto de estilos del CSS anterior si ves que no cargan */
      `;
      doc.head.appendChild(styleTag);

      // Dentro de la función tippy(...) en handleIframeLoad
      tippy(doc.querySelectorAll('.badge, strong[title]'), {
        content(reference) {
          const title = reference.getAttribute('tit');
          if (!title) return '';

          const parts = title.split(' ');
          if (parts.length >= 3) {
            const sujeto = parts[0];
            const propiedad = parts[1];
            const objeto = parts.slice(2).join(' ');

            return `
              <div style="text-align: left; padding: 5px; min-width: 150px;">
                <div style="color: #bbb; font-size: 0.7rem; margin-bottom: 2px;">${sujeto}</div>
                <div style="color: #1976d2; font-weight: bold; font-size: 0.85rem; border-top: 1px solid #444; border-bottom: 1px solid #444; padding: 3px 0; margin: 3px 0;">
                  ${propiedad}
                </div>
                <div style="color: #bbb; font-size: 0.7rem; margin-top: 2px;">${objeto}</div>
              </div>
            `;
          }
          return title;
        },
        allowHTML: true,
        theme: 'custom-opaque', // Nombre de nuestro nuevo tema
        placement: 'top',
        interactive: true,
        appendTo: doc.body,
      });
    }
  };

  if (!html) return <div className="loading-visor">Cargando contenido...</div>;

  return (
    <div className="visor-container" style={{ padding: "20px", height: "85vh" }}>
      <iframe
        ref={iframeRef}
        srcDoc={html}
        title={titulo}
        onLoad={handleIframeLoad} // Disparamos la lógica al cargar
        style={{
          width: "100%",
          height: "100%",
          border: "1px solid #ddd",
          borderRadius: "8px",
          backgroundColor: "#fff"
        }}
      />
    </div>
  );
}