import { ForceGraph2D } from 'react-force-graph';
import React, { useMemo, useRef, useState, useEffect } from 'react';
import { FiShare2, FiMaximize } from 'react-icons/fi';
import { useApp } from '../../AppContext'; 

const VisualizadorGrafo = ({ data }) => {
  const { t } = useApp();
  const fgRef = useRef();
  //const containerRef = useRef(); // Referencia para medir el contenedor
  const [zoomPercent, setZoomPercent] = useState(100);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  const gData = useMemo(() => ({
    nodes: data.nodos.map(n => ({
      id: n.nombre,
      etiquetas: n.etiquetas,
      propiedades: n.propiedades 
    })),
    links: data.relaciones.map(r => ({
      source: r.origen,
      target: r.destino,
      label: r.relacion?.replace(/ns0__/g, '') || "",
      tipo: r.tipo,
      texto_ref: r.texto_ref
    }))
  }), [data]);

  useEffect(() => {
    if (fgRef.current && gData.nodes.length > 0) {
      // FUERZAS PARA MÁXIMA EXPANSIÓN
      // Aumentamos la repulsión para que los nodos se separen más
      fgRef.current.d3Force('charge').strength(-1200);
      
    //   // Fuerza de centrado para que no se pierdan fuera del lienzo
    //   fgRef.current.d3Force('center').strength(0.05);
      
      // Forzamos el centro exacto basado en las dimensiones del canvas
      fgRef.current.d3Force('center', window.d3?.forceCenter(graphWidth / 2, graphHeight / 2));
      
      // Añadimos colisión para evitar solapamientos
      fgRef.current.d3Force('collide', window.d3?.forceCollide(35));

      setTimeout(() => {
        // Ajuste con padding mínimo (10px) para ocupar todo el espacio
        if (fgRef.current && typeof fgRef.current.zoomToFit === 'function') {
          fgRef.current.zoomToFit(600, 50); // 600ms de animación, 50px de padding
        }
        setZoomPercent(Math.round(fgRef.current.zoom() * 100));
      }, 800);
    }
  }, [gData, dimensions]);

  // 1. EFECTO PARA MEDIR EL CONTENEDOR AUTOMÁTICAMENTE
  useEffect(() => {
    const updateSize = () => {
      if (fgRef.current) {
        // setDimensions({
        //   width: fgRef.current.offsetWidth,
        //   height: fgRef.current.offsetHeight
        // });
        setDimensions({
          width:  window.innerWidth,
          height:  window.innerWidth
        });
        console.log("Dimension: " + fgRef.current.offsetWidth + ":" + fgRef.current.offsetHeight)
        console.log("Other dimensions" + window.innerWidth + ":" + window.innerHeight)
      }
    };
    console.log("Hola caracola" + fgRef.current)
    // Medimos al montar
    updateSize();

    // Volvemos a medir si la ventana cambia de tamaño
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Definimos una función para determinar el color según el tipo
  const getColorPorTipo = (tipo) => {
    const t = tipo?.toString().toLowerCase().trim();
    if (t === 'necessary') return '#006400'; // Verde (o el color que prefieras para "ok")
    if (t === 'surplus') return '#ff9800';   // Naranja
    if (t === 'created') return '#FF0000';   // Rojo
    return '#808080'; // Color por defecto (el lila que tenías)
  };

  const handleZoom = (transform) => {
    setZoomPercent(Math.round(transform.k * 100));
  };

  return (
    // <div className="resultado-card" style={{ height: '500px', padding: '0', position: 'relative', overflow: 'hidden' }}>
    <div className="resultado-card" style={{ padding: '0', position: 'relative', overflow: 'hidden' }}>
      {/* Controles de Zoom e Info */}
      <div style={{ position: 'absolute', top: 15, right: 15, zIndex: 10, display: 'flex', gap: '10px' }}>
        <div style={{ background: '#1976d2', color: 'white', padding: '5px 15px', borderRadius: '20px', fontWeight: 'bold', boxShadow: '0 2px 5px rgba(0,0,0,0.2)' }}>
          Zoom: {zoomPercent}%
        </div>
      </div>

      {/* <button 
        onClick={() => fgRef.current.zoomToFit(500, 10)}
        style={{ position: 'absolute', top: '20px', left: '20px', padding: '10px 20px', backgroundColor: '#fff', border: '1px solid #1976d2', borderRadius: '30px', color: '#1976d2', fontWeight: 'bold', cursor: 'pointer', zIndex: 10 }}
      >
        <FiMaximize /> {t('grafo.adjust')}
      </button> */}

      <ForceGraph2D
        ref={fgRef}
        graphData={gData}
        width={window.innerWidth * 0.9} 
        flex={1}// height={500}
        height={window.innerHeight * 0.9}
        onZoom={handleZoom}
        d3AlphaDecay={0.05} // Simulación más lenta para que se expandan mejor
        d3VelocityDecay={0.7}
        cooldownTicks={150}
        
        // --- RENDERIZADO DE NODOS CON TEXTO FIJO ---
        nodeCanvasObject={(node, ctx, globalScale) => {
          // 2. Recortar nombre visual a 10 caracteres
          const labelCompleto = node.id;
          const labelVisual = labelCompleto.length > 8 
            ? labelCompleto.substring(0, 8) + '...' 
            : labelCompleto;
          // Dividimos por globalScale para que el tamaño visual sea siempre el mismo
          const fontSize = 14 / globalScale; 
          ctx.font = `${fontSize}px Sans-Serif`;

          // --- LÓGICA DE COLORES POR PRELACIÓN ---
        let colorNodo = "#1976d2"; // Azul por defecto

        if (node.id?.toLowerCase() === "no_name") {
            colorNodo = "#9e9e9e"; // Gris para nodos sin nombre
        } else if (node.etiquetas?.includes("Report")) {
            colorNodo = "#ec7c26"; // Verde para Report
        } else if (node.etiquetas?.includes("StolenGoods")) {
            colorNodo = "#e8cd61"; // Naranja para StoolenGoods
        } else if (node.etiquetas?.includes("Accused")) {
            colorNodo = "#f44336"; // Rojo para Accused
        } else if (node.etiquetas?.includes("Victim")) {
            colorNodo = "#03BB85"; // Rojo para Victim
        } 
          
          // Círculo del nodo
          const radioNodo = 10; // Aumenta este número para un círculo más grande
          ctx.beginPath();
          ctx.arc(node.x, node.y, radioNodo, 0, 2 * Math.PI, false);
          ctx.fillStyle = colorNodo;
          ctx.fill();

          // 3. Posicionar nombre a un lado del nodo
          // Determinamos si el texto va a la derecha o izquierda según su posición en el lienzo
          const sidePadding = (radioNodo + 5) / globalScale;
          const textX = node.x + sidePadding;

          ctx.textAlign = 'left';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = '#333';
          ctx.fillText(labelVisual, textX, node.y);
        }}

        // --- RENDERIZADO DE RELACIONES CON TEXTO FIJO ---
        linkCanvasObjectMode={() => 'after'}
        linkCurvature={0.2}
        linkDirectionalArrowLength={3}

        // Aplicamos el color a la línea de la relación
        linkColor={link => getColorPorTipo(link.tipo)}
        
        // Aplicamos el color a la flecha
        linkDirectionalArrowColor={link => getColorPorTipo(link.tipo)}


        linkCanvasObject={(link, ctx, globalScale) => {
          const label = link.label;
          const fontSize = 12 / globalScale; // Tamaño constante
          ctx.font = `${fontSize}px Sans-Serif`;
          
          const start = link.source;
          const end = link.target;
          const textPos = {
            x: start.x + (end.x - start.x) / 2,
            y: start.y + (end.y - start.y) / 2
          };

          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = '#666';
          // Fondo blanco para legibilidad del tipo de relación
          const textWidth = ctx.measureText(label).width;
          ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
          ctx.fillRect(textPos.x - textWidth / 2, textPos.y - fontSize / 2, textWidth, fontSize);
          
          ctx.fillStyle = '#d32fba'; // Color distintivo para la relación
          ctx.fillText(label, textPos.x, textPos.y);
        }}
        
        

        nodeLabel={node => `
        <div style="background: rgba(0,0,0,0.85); color: #fff; padding: 10px; border-radius: 6px; border: 1px solid #1976d2;">
            <strong style="color: #64b5f6; font-size: 13px;">ID:</strong> ${node.id}<br/>
            <strong style="color: #ffb74d;">Etiquetas:</strong> ${node.etiquetas}<br/>
            <hr style="margin: 5px 0; border-top: 1px solid #555" />
            <small>${node.propiedades || 'Sin propiedades'}</small>
        </div>
        `}

        // linkLabel={link => `
        // <div style="background: rgba(45,45,45,0.9); color: #fff; padding: 8px; border-radius: 4px; border: 1px solid #f44336;">
        //     <strong>Relación:</strong> ${link.label}<br/>
        //     <hr style="margin: 5px 0; border-top: 1px solid #666" />
        //     <div style="font-size: 11px; font-style: italic; max-width: 250px;">
        //     ${link.texto_ref || 'Ver tabla para más detalles'}
        //     </div>
        // </div>
        // `}
        // --- DENTRO DE ForceGraph2D ---
        linkLabel={link => {
          // Verificamos si los datos existen y no son "None" o vacíos
          const tieneTipo = link.tipo && link.tipo.toString().toLowerCase() !== 'none' && link.tipo !== "";
          const tieneRef = link.texto_ref && link.texto_ref.toString().toLowerCase() !== 'none' && link.texto_ref !== "";

          return `
            <div style="background: rgba(45,45,45,0.95); color: #fff; padding: 12px; border-radius: 8px; border: 1px solid #1976d2; box-shadow: 0 4px 15px rgba(0,0,0,0.3); font-family: sans-serif;">
                <strong style="color: #64b5f6; font-size: 13px;">Relación:</strong> 
                <span style="font-size: 13px;">${link.label}</span>
                
                <hr style="margin: 8px 0; border: 0; border-top: 1px solid #555" />
                
                ${tieneTipo ? `
                  <div style="margin-bottom: 5px;">
                    <strong style="color: #81c784;">Tipo:</strong> ${link.tipo}
                  </div>
                ` : ''}

                ${tieneRef ? `
                  <div style="max-width: 300px; line-height: 1.4;">
                    <strong style="color: #ffb74d;">Referencias:</strong> 
                    <div style="font-size: 11px; font-style: italic; margin-top: 4px; color: #ddd; background: rgba(0,0,0,0.2); padding: 5px; border-radius: 4px;">
                      ${link.texto_ref}
                    </div>
                  </div>
                ` : ''}
                
                ${!tieneTipo && !tieneRef ? '<small style="color: #888;">Sin detalles adicionales</small>' : ''}
            </div>
          `;
        }}
      />
    </div>
  );
};

export default VisualizadorGrafo;