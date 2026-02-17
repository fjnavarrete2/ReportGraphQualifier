import React, { useMemo, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  useReactTable, 
  getCoreRowModel, 
  getFilteredRowModel, 
  getPaginationRowModel, 
  flexRender 
} from '@tanstack/react-table';
import { FiArrowLeft, FiSearch, FiLayers, FiShare2 } from 'react-icons/fi';

// IMPORTACIONES PARA EL TOOLTIP
import Tippy from '@tippyjs/react';
import 'tippy.js/dist/tippy.css';
import 'tippy.js/animations/shift-away.css';

import './Analizador.css';
import VisualizadorGrafo from './VisualizadorGrafo';
import { useApp } from '../../AppContext';

// Componente de Tabla Genérico para reutilizar
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
    initialState: {
      pagination: {
        pageSize: 10, 
      },
    },
  });

  return (
    <div className="resultado-card" style={{ maxWidth: '100%', marginBottom: '30px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
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

      <div className="table-responsive">
        <table className="status-table">
          <thead>
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th key={header.id}>
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
                  <td key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pagination-controls" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '15px' }}>
        <div className="page-size-selector">
          <span style={{ fontSize: '0.85rem', marginRight: '8px' }}>{t('common.pagination.show')}</span>
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
          <button onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
            {t('common.pagination.prev')}
          </button>
          <span style={{ margin: '0 10px', fontSize: '0.85rem' }}>
           {t('common.pagination.page_of')} {table.getState().pagination.pageIndex + 1} {t('common.pagination.page_of2')} {table.getPageCount()}
          </span>
          <button onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>{t('common.pagination.next')}</button>
        </div>
      </div>
    </div>
  );
};


export default function ResumenGrafo() {
  const navigate = useNavigate();
  const { t } = useApp();
  const [data, setData] = useState({ nodos: [], relaciones: [] });
  const [nombreAtestado, setNombreAtestado] = useState("");

  useEffect(() => {
    const raw = sessionStorage.getItem('datos_resumen_grafo');
    if (raw) {
      const parsedData = JSON.parse(raw);
      
      const relacionesFormateadas = (parsedData.relaciones || []).map(rel => ({
            referencia: rel[0],
            origen: rel[1],
            relacion: rel[2],
            destino: rel[3],
            texto_ref: rel[4],
            tipo: rel[5],
          }));

      const nodosFormateados = (parsedData.nodos || []).map(nodo => ({
        nombre: nodo[0],
        etiquetas: nodo[1],
        propiedades: nodo[2]
      }));

      setNombreAtestado(parsedData.name || "");
      setData({
        relaciones: relacionesFormateadas,
        nodos: nodosFormateados
      });
    }
  }, []);

  // FUNCIÓN AUXILIAR PARA RENDERIZAR LAS LÍNEAS SEPARADAS POR |
  const renderMultiLineTooltip = (texto) => {
    if (!texto) return null;
    const frases = texto.split('|');
    
    return (
      <div style={{ textAlign: 'left', padding: '5px' }}>
        {frases.map((frase, index) => (
          <div key={index} style={{ 
            marginBottom: index === frases.length - 1 ? 0 : '8px',
            fontSize: '0.8rem',
            lineHeight: '1.4',
            borderLeft: '2px solid #1976d2', // Pequeño detalle visual azul
            paddingLeft: '8px'
          }}>
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
                        <span className="ref-circle-badge" style={{ cursor: 'pointer' }}>
                            {valor}
                        </span>
                      </Tippy>
                  </div>
              );
          }
      },
    { header: t('grafo.cols.origin'), accessorKey: 'origen' },
    { header: t('grafo.cols.relation'), accessorKey: 'relacion', cell: info => <span className="badge-rel">{info.getValue()?.replace(/ns0__/g, '')}</span> },
    { header: t('grafo.cols.dest'), accessorKey: 'destino' },
  ], [t]);

  const colNodos = useMemo(() => [
    { header: t('grafo.cols.element'), accessorKey: 'nombre', cell: info => <strong>{info.getValue()}</strong> },
    { header: t('grafo.cols.labels'), accessorKey: 'etiquetas' },
    { header: t('grafo.cols.props'), accessorKey: 'propiedades', cell: info => <span style={{ fontSize: '0.8rem', color: '#666' }}>{info.getValue()}</span> },
  ], [t]);

  return (
  <div className="atestados-wrapper full-width">
    <div className="header-view">
      <button className="btn archivo-btn" onClick={() => navigate('/analizador')}>
        <FiArrowLeft /> {t('common.back')}
      </button>
      <h1>{t('resumen_tabla.summary_view_title')} {nombreAtestado ? `'${nombreAtestado}'` : ''}</h1>
    </div>

    <div className="resumen-container-vertical" style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      <div style={{ width: '100%', height: '500px', background: '#fff', borderRadius: '8px', border: '1px solid #ddd', overflow: 'hidden' }}>
        <VisualizadorGrafo data={data} />
      </div>

      <DataTable 
        title={t('resumen_tabla.panel.rows.summary')}
        data={data.relaciones} 
        columns={colRelaciones} 
        icon={FiShare2} 
      />

      <DataTable 
        title={t('resumen_tabla.panel.rows.nodes')}
        data={data.nodos} 
        columns={colNodos} 
        icon={FiLayers} 
      />
      
    </div>
  </div>
);
}