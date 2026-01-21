import React, { useMemo, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios'; // 1. IMPORTACIÓN FALTANTE
import { 
  useReactTable, 
  getCoreRowModel, 
  getFilteredRowModel, 
  getPaginationRowModel, 
  flexRender 
} from '@tanstack/react-table';
// 2. AÑADIDOS FiX y FiLoader
import { FiArrowLeft, FiSearch, FiActivity, FiList, FiX, FiLoader, FiShare2, FiLayers, FiGitCommit } from 'react-icons/fi';
import { useApp } from '../../AppContext'; // 3. IMPORTACIÓN DEL CONTEXTO
import './Analizador.css';
import VisualizadorGrafo from './VisualizadorGrafo'; // Importante para el modal

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
      {/* Controles de paginación se mantienen igual */}
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
  const [data, setData] = useState({ resultados: [] });
  
  // 4. USAMOS EL CONTEXTO EN LUGAR DE LOCALSTORAGE PARA SEGURIDAD
  const { debugJson } = useApp();

  // ESTADOS PARA EL MODAL
  const [modalOpen, setModalOpen] = useState(false);
  const [loadingModal, setLoadingModal] = useState(false);
  const [datosResumen, setDatosResumen] = useState(null);
  const [articuloSeleccionado, setArticuloSeleccionado] = useState("");
  const [modalView, setModalView] = useState(""); // "grafo" o "resumen"
  const [nombreAtestado, setNombreAtestado] = useState("");

  useEffect(() => {
    const raw = sessionStorage.getItem('datos_resultado_grafo');
    if (raw) {
      const parsedData = JSON.parse(raw);
      const resultadosFormateados = (parsedData.resultados_probabilidad || []).map(rel => ({
        articulo: rel[0],
        probabilidad: rel[1],
        incertidumbre: rel[2],
        propiedades: rel[4]
      }));
      setNombreAtestado(parsedData.name || "");
      setData({ resultados: resultadosFormateados });
    }
  }, []);


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
        //formateo
        const parsedData = response.data;
        // Transformamos los arrays de Relaciones a Objetos
        const relacionesFormateadas = (parsedData.relaciones || []).map(rel => ({
          referencia: rel[0],
          origen: rel[1],
          relacion: rel[2],
          destino: rel[3],
          tipo: rel[4],
          texto_ref: rel[5]
        }));

        // Transformamos los arrays de Nodos a Objetos
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

  // Definición de columnas para las tablas dentro del modal
  const colRelaciones = useMemo(() => [
          { 
          header: t('grafo.cols.ref'), 
          accessorKey: 'referencia', 
          cell: (info) => {
              const valor = info.getValue();
              const textoReferencia = info.row.original.texto_ref; // Asumiendo que texto_ref es un string directo del objeto

              // Validamos si el valor es nulo, vacío o la palabra "none"
              if (!valor || valor.toString().toLowerCase() === 'none' || valor.toString().trim() === '') {
                  return null; // No renderiza nada en la celda
              }

              return (
                  <div className="ref-circle-container">
                      <span 
                          className="ref-circle-badge" 
                          title={textoReferencia} 
                      >
                          {valor}
                      </span>
                  </div>
              );
          }
      },
    { header: t('grafo.cols.origin'), accessorKey: 'origen' },
    { header: t('grafo.cols.relation'), accessorKey: 'relacion', cell: info => info.getValue()?.replace(/ns0__/g, '') },
    { header: t('grafo.cols.dest'), accessorKey: 'destino' },
    { 
    header: t('grafo.type'), 
    accessorKey: 'tipo', // Usamos el campo tipo para aplicar el color
    cell: info => {
      const tipo = info.getValue()?.toString().toLowerCase().trim();
      let color = 'black'; // Color por defecto

      if (tipo === 'necessary') color = '#28a745';      // Verde
      else if (tipo === 'surplus') color = '#e67e22';   // Naranja oscuro
      else if (tipo === 'created') color = '#dc3545';   // Rojo

      return (
        <span style={{ color: color, fontWeight: '600' }}>
          {/* Mostramos el nombre de la relación (r.relacion) pero con el color del tipo */}
          {info.getValue()}
        </span>
      );
    }
  },,
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
    // { 
    //   header: t('resultado.col_uncert'), 
    //   accessorKey: 'incertidumbre',
    //   meta: { headerClass: 'col-porcentaje', cellClass: 'col-porcentaje' },
    //   cell: info => `${(parseFloat(info.getValue()) * 100).toFixed(2)}%`
    // },
    { 
      header: t('resultado.col_props'), 
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
          onClick={() => abrirModal(info.row.original.articulo, 'resumen')} //abrirResumenArticulo(info.row.original.articulo)}
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
  ], [loadingModal, articuloSeleccionado]);

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
          <div className="modal-content full-screen">
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
                <div className="fade-in">
                  {modalView === 'grafo' ? (
                    //<div style={{ height: 'calc(100vh - 0px)', background: '#fff', border: '1px solid #ddd' }}>
                    <div className="canvas-container-modal">
                      <VisualizadorGrafo data={datosResumen} />
                    </div>
                  ) : (
                    /* --- VISTA RESUMEN: TABLAS A TODA ANCHURA --- */
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