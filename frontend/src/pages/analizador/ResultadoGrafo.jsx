import React, { useMemo, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  useReactTable, 
  getCoreRowModel, 
  getFilteredRowModel, 
  getPaginationRowModel, 
  flexRender 
} from '@tanstack/react-table';
import { FiArrowLeft, FiSearch, FiActivity, FiList, FiX, FiLoader, FiShare2, FiLayers, FiGitCommit, FiInfo } from 'react-icons/fi';

// Importaciones para el tooltip
import Tippy from '@tippyjs/react';
import 'tippy.js/dist/tippy.css';
import 'tippy.js/animations/shift-away.css';

import { useApp } from '../../AppContext';
import './Analizador.css';
import VisualizadorGrafo from './VisualizadorGrafo';



const DataTable = ({ data, columns, title, icon: Icon }) => {
  const { t } = useApp();
  const [globalFilter, setGlobalFilter] = useState('');

  const table = useReactTable({
    data,
    columns,
    state: { globalFilter },
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 10 } },
  });

  return (
    <div className="resultado-card resultado-tabla-wrapper">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
        <h3><Icon style={{ marginRight: '10px' }} /> {title}</h3>
        <div className="search-container">
          <FiSearch />
          <input
            value={globalFilter ?? ''}
            onChange={e => setGlobalFilter(e.target.value)}
            placeholder={t('common.search')}
            className="table-search-input"
          />
        </div>
      </div>
      <table className="status-table">
        <thead>
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map(header => (
                <th key={header.id} className={header.column.columnDef.meta?.headerClass}>
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map(row => (
            <tr key={row.id}>
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className={cell.column.columnDef.meta?.cellClass}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      
      <div className="pagination-controls" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '15px' }}>
        <div className="page-size-selector">
          <span style={{ fontSize: '0.85rem', marginRight: '8px' }}>
            {t('common.pagination.show')}
          </span>
          <select
            value={table.getState().pagination.pageSize}
            onChange={e => {
              table.setPageSize(Number(e.target.value))
            }}
            className="select-pagination"
          >
            {[5, 10, 20, 50].map(pageSize => (
              <option key={pageSize} value={pageSize}>
                {pageSize} {t('common.pagination.rows')}
              </option>
            ))}
          </select>
        </div>
        <div className="pagination-navigation">
          <button onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>Anterior</button>
          <span style={{ margin: '0 10px', fontSize: '0.85rem' }}>
            {t('common.pagination.page_of')} {table.getState().pagination.pageIndex + 1} {t('common.pagination.page_of2')} {table.getPageCount()}
          </span>
          <button onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
            {t('common.pagination.next')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default function ResultadoGrafo() {
  const navigate = useNavigate();
  const { t } = useApp();
  const { debugJson } = useApp();

  const [modalOpen, setModalOpen] = useState(false);
  const [loadingModal, setLoadingModal] = useState(false);
  const [datosResumen, setDatosResumen] = useState(null);
  const [articuloSeleccionado, setArticuloSeleccionado] = useState("");
  const [modalView, setModalView] = useState(""); 

  const [data, setData] = useState(() => {
    const raw = sessionStorage.getItem('datos_resultado_grafo');
    if (raw) {
      const parsedData = JSON.parse(raw);
      return {
        resultados: (parsedData.resultados_probabilidad || []).map(rel => ({
          articulo: rel[0],
          probabilidad: rel[1],
          incertidumbre: rel[2],
          propiedades: rel[4]
        }))
      };
    }
    return { resultados: [] };
  });

  const [nombreAtestado, setNombreAtestado] = useState(() => {
    const raw = sessionStorage.getItem('datos_resultado_grafo');
    if (raw) {
      return JSON.parse(raw).name || "";
    }
    return "";
  });

  // Componente Leyenda para la columna Incertidumbre
  const LeyendaIncertidumbre = () => (
    <Tippy
      theme="custom-opaque"
      animation="shift-away"
      interactive={true}
      placement="bottom-start"
      maxWidth={300}
      content={
         <div style={{ padding: '8px', textAlign: 'left', fontFamily: 'Segoe UI, sans-serif' }}>
          <div style={{ 
            marginBottom: '8px', 
            fontWeight: 'bold', 
            color: '#1976d2', 
            borderBottom: '1px solid #555', 
            paddingBottom: '4px',
            fontSize: '0.9rem'
          }}>
            {t('resultado.info_caracteristica.titulo')}
          </div>
          
          <div style={{ marginBottom: '8px', display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
            <span style={{ color: '#28a745', fontSize: '1rem', marginTop: '1px' }}>●</span>
            <span style={{ fontSize: '0.8rem', color: '#eee', lineHeight: '1.4' }}>
              <strong style={{ color: '#28a745' }}>{t('resultado.info_caracteristica.cabecera_presente')}</strong>
              {t('resultado.info_caracteristica.cuerpo_presente')}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
            <span style={{ color: '#dc3545', fontSize: '1rem', marginTop: '1px' }}>●</span>
            <span style={{ fontSize: '0.8rem', color: '#eee', lineHeight: '1.4' }}>
              <strong style={{ color: '#dc3545' }}>{t('resultado.info_caracteristica.cabecera_ausente')}</strong>
              {t('resultado.info_caracteristica.cuerpo_ausente')}
              <u>{t('resultado.info_caracteristica.cuerpo_ausente2')}</u>
              {t('resultado.info_caracteristica.cuerpo_ausente3')}
            </span>
          </div>
        </div>
      }
    >
      <div style={{ 
        display: 'inline-flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        cursor: 'help', 
        marginLeft: '6px',
        color: '#666',
        transition: 'color 0.2s',
        verticalAlign: 'middle'
      }}
      onMouseEnter={(e) => e.currentTarget.style.color = '#1976d2'}
      onMouseLeave={(e) => e.currentTarget.style.color = '#666'}
      title="" // Eliminamos title nativo para que no moleste
      >
        <FiInfo size={16} />
      </div>
    </Tippy>
  );

  const abrirModal = async (articuloOriginal, tipoVista) => {
    setArticuloSeleccionado(articuloOriginal.replace(/ns0__/g, ''));
    setModalView(tipoVista);
    setLoadingModal(true);
    setModalOpen(true);
    setDatosResumen(null);

    try {
      const formData = new FormData();
      formData.append("root_name", nombreAtestado); 
      formData.append("article", articuloOriginal.replace(/ns0__/g, ''));
      
      const response = await axios.post("http://localhost:8000/recuperarTuplasGrafo/", formData);
      if (response.data.status === "ok") {
        const parsedData = response.data;
        const relacionesFormateadas = (parsedData.relaciones || []).map(rel => ({
          referencia: rel[0],
          origen: rel[1],
          relacion: rel[2],
          destino: rel[3],
          tipo: rel[4],
          texto_ref: rel[5]
        }));

        const nodosFormateados = (parsedData.nodos || []).map(nodo => ({
          nombre: nodo[0],
          etiquetas: nodo[1],
          propiedades: nodo[2]
        }));
        setDatosResumen({
          relaciones: relacionesFormateadas,
          nodos: nodosFormateados
        });
      } else {
        alert("El servidor no devolvió datos válidos");
        setModalOpen(false);
      }
    } catch (err) {
      console.error("Error al obtener resumen:", err);
      alert("Error de conexión");
      setModalOpen(false);
    } finally {
      setLoadingModal(false);
    }
  };

  const renderMultiLineTooltip = (texto) => {
    if (!texto) return null;
    const frases = texto.split('|');
    return (
      <div style={{ textAlign: 'left', padding: '5px' }}>
        {frases.map((frase, index) => (
          <div key={index} style={{ marginBottom: '8px', fontSize: '0.8rem', borderLeft: '2px solid #1976d2', paddingLeft: '8px' }}>
            {frase.trim()}
          </div>
        ))}
      </div>
    );
  };

  const colRelaciones = useMemo(() => [
    { 
      header: t('grafo.cols.ref'), 
      accessorKey: 'referencia', 
      cell: (info) => {
          const valor = info.getValue();
          const textoReferencia = info.row.original.texto_ref; 

          if (!valor || valor.toString().toLowerCase() === 'none' || valor.toString().trim() === '') {
              return null; 
          }

          return (
              <div className="ref-circle-container">
                  <Tippy 
                    content={renderMultiLineTooltip(textoReferencia)} 
                    theme="custom-opaque" 
                    animation="shift-away"
                    allowHTML={true}
                    maxWidth={400}
                    interactive={true}
                  >
                    <span className="ref-circle-badge" style={{ cursor: 'zoom-in' }}>
                        {valor}
                    </span>
                  </Tippy>
              </div>
          );
      }
    },
    { header: t('grafo.cols.origin'), accessorKey: 'origen' },
    { header: t('grafo.cols.relation'), accessorKey: 'relacion', cell: info => info.getValue()?.replace(/ns0__/g, '') },
    { header: t('grafo.cols.dest'), accessorKey: 'destino' },
    { 
      header: t('grafo.type'), 
      accessorKey: 'tipo', 
      cell: info => {
        const tipo = info.getValue()?.toString().toLowerCase().trim();
        let color = 'black'; 

        if (tipo === 'necessary') color = '#28a745';      
        else if (tipo === 'surplus') color = '#e67e22';   
        else if (tipo === 'created') color = '#dc3545';   

        return (
          <span style={{ color: color, fontWeight: '600' }}>
            {info.getValue()}
          </span>
        );
      }
    },
  ], []);

  const colNodos = useMemo(() => [
      { header: t('grafo.cols.element'), accessorKey: 'nombre', cell: info => <strong>{info.getValue()}</strong> },
      { header: t('grafo.cols.labels'), accessorKey: 'etiquetas' },
      { header: t('grafo.cols.props'), accessorKey: 'propiedades', cell: info => <span style={{ fontSize: '0.8rem', color: '#666' }}>{info.getValue()}</span> },
    ], []);

  const colResultados = useMemo(() => [
    { 
      header: t('resultado.col_article'), 
      accessorKey: 'articulo',
      meta: { cellClass: 'col-articulo' },
      cell: info => info.getValue()?.replace(/ns0__/g, '')
    },
    { 
      header: t('resultado.col_prob'), 
      accessorKey: 'probabilidad',
      meta: { headerClass: 'col-porcentaje', cellClass: 'col-porcentaje' },
      cell: info => `${(parseFloat(info.getValue()) * 100).toFixed(2)}%`
    },
    { 
      header: () => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {t('resultado.col_props')}
          <LeyendaIncertidumbre />
        </div>
      ),
      accessorKey: 'propiedades',
      cell: info => {
        const val = info.getValue();
        if (!val) return null;
        const cleanStr = JSON.stringify(val).replace(/[{}]/g, '').replace(/"/g, '');
        const pairs = cleanStr.split(',');

        return (
          <div className="propiedades-contenedor">
            {pairs.map((pair, idx) => {
              const [key, value] = pair.split(':');
              const valTrim = value?.trim().toLowerCase();
              return (
                <span key={idx} className="prop-item">
                  <span className={valTrim === 'known' ? 'prop-clave-known' : valTrim === 'unknown' ? 'prop-clave-unknown' : ''}>
                    {key?.trim()}
                  </span>
                  {idx < pairs.length - 1 ? ',' : ''}
                </span>
              );
            })}
          </div>
        );
      }
    },
    {
      header: t('resultado.col_summary'),
      id: 'btn-resumen',
      meta: { headerClass: 'col-centro', cellClass: 'col-centro' },
      cell: info => (
        <button 
          className="btn-resumen-tabla" 
          title="Ver tabla de resumen" 
          onClick={() => abrirModal(info.row.original.articulo, 'resumen')} 
        >
          {loadingModal && articuloSeleccionado === info.row.original.articulo.replace(/ns0__/g, '') ? 
            <FiLoader className="spinner-icon" /> : <FiList />
          }
        </button>
      )
    },
    {
      header: t('resultado.col_graph'),
      id: 'btn-grafo',
      cell: info => (
        <button className="btn-resumen-tabla" onClick={() => abrirModal(info.row.original.articulo, 'grafo')}>
          <FiGitCommit />
        </button>
      )
    }
  ], [loadingModal, articuloSeleccionado, t]);

  return (
    <div className="atestados-wrapper full-width">
      <div className="header-view">
        <button className="btn archivo-btn" onClick={() => navigate('/analizador')}>
          <FiArrowLeft /> {t('common.back')}
        </button>
        <h1>{t('resultado.title')} {nombreAtestado ? `'${nombreAtestado}'` : ''}</h1>
      </div>

      <div className="main-content">
        <DataTable 
          title={t('resultado.prob_table_title')} 
          data={data.resultados} 
          columns={colResultados} 
          icon={FiActivity} 
        />
      </div>
      
      {/* VENTANA MODAL */}
      {modalOpen && (
        <div className="modal-overlay">
          <div className="modal-container">
            <div className="modal-header">
              <h2>
                {modalView === 'grafo' ? <FiGitCommit /> : <FiList />} 
                {modalView === 'grafo' ? t('resultado.modal.graph_title') : t('resultado.modal.summary_title')} 
                <span style={{color: '#1976d2'}}>{articuloSeleccionado} {t('resultado.modal.for')} '{nombreAtestado}'</span>
              </h2>
              <button className="modal-close" onClick={() => setModalOpen(false)}><FiX /></button>
            </div>
            
            <div className="modal-body">
              {loadingModal ? (
                <div className="modal-loader"><div className="spinner" /><p>{t('common.loading')}</p></div>
              ) : datosResumen ? (
                <div className="fade-in" style={{ flex: 1, display: 'flex' }}>
                  {modalView === 'grafo' ? (
                    <div className="canvas-container-modal">
                      <VisualizadorGrafo data={datosResumen} />
                    </div>
                  ) : (
                    <div className="full-width-tables" style={{ display: 'flex', flexDirection: 'column', gap: '5px', width: '100%' }}>
                      <DataTable 
                        title={t('resultado.modal.ontology_rel')}
                        data={datosResumen.relaciones} 
                        columns={colRelaciones} 
                        icon={FiShare2} 
                      />
                      <DataTable 
                        title={t('resultado.modal.entities_nodes')}
                        data={datosResumen.nodos} 
                        columns={colNodos} 
                        icon={FiLayers} 
                      />
                    </div>
                  )}
                </div>
              ) : null}
            </div>
            <div className="modal-footer">
              <button className="btn-cerrar-modal" onClick={() => setModalOpen(false)}>Cerrar Ventana</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}