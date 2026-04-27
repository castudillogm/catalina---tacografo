import React, { useState, useEffect } from 'react';
import * as XLSX from 'xlsx';
import { 
  FileSpreadsheet, 
  Upload, 
  Download, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  Calendar,
  Coffee,
  Trash2,
  ChevronRight,
  Truck
} from 'lucide-react';
import { processTacografoData } from './utils/tacografoLogic';
import './index.css';

const App = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ totalDays: 0, totalBreaks: '00:00', avgHours: '00:00' });

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    processFile(file);
  };

  const processFile = (file) => {
    setLoading(true);
    setError(null);
    const reader = new FileReader();

    reader.onload = (evt) => {
      try {
        const bstr = evt.target.result;
        const wb = XLSX.read(bstr, { type: 'binary', cellDates: true });
        const wsname = wb.SheetNames[0];
        const ws = wb.Sheets[wsname];
        
        // Robustly find the header row
        const fullData = XLSX.utils.sheet_to_json(ws, { header: 1 });
        const headerRowIndex = fullData.findIndex(row => 
          row.includes('Tarjeta') && row.includes('Actividad') && (row.includes('Inicio') || row.includes('Comienzo'))
        );

        if (headerRowIndex === -1) {
          throw new Error('No se pudo encontrar la fila de encabezados (Tarjeta, Actividad, Inicio).');
        }

        const rawData = XLSX.utils.sheet_to_json(ws, { range: headerRowIndex });
        const processed = processTacografoData(rawData);
        
        if (processed.length === 0) {
          throw new Error('No se encontraron datos válidos. Verifica el formato del archivo.');
        }

        setData(processed);
        calculateStats(processed);
      } catch (err) {
        console.error(err);
        setError(err.message || 'Error al procesar el archivo');
      } finally {
        setLoading(false);
      }
    };

    reader.onerror = () => {
      setError('Error al leer el archivo');
      setLoading(false);
    };

    reader.readAsBinaryString(file);
  };

  const calculateStats = (processed) => {
    const totalDays = processed.length;
    // Simple average calculation for demo
    setStats({
      totalDays,
      totalBreaks: processed.reduce((acc, curr) => acc + (curr.Descansos !== '00:00' ? 1 : 0), 0) + ' días con desc.',
      avgHours: 'Jornada procesada'
    });
  };

  const exportToExcel = () => {
    const ws = XLSX.utils.json_to_sheet(data.map(({ _rawDate, ...rest }) => rest));
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Jornadas");
    XLSX.writeFile(wb, "Tacografo_Tratado.xlsx");
  };

  const reset = () => {
    setData(null);
    setError(null);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const onDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  };

  return (
    <div className="min-h-screen p-4 md:p-8 flex flex-col items-center">
      {/* Header */}
      <header className="w-full max-w-6xl flex justify-between items-center mb-12 animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="p-3 glass-card bg-indigo-600/20 rounded-2xl">
            <Truck className="w-8 h-8 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gradient">Tacógrafo Pro</h1>
            <p className="text-gray-400 text-sm">Procesador Inteligente de Actividades</p>
          </div>
        </div>
        {data && (
          <button onClick={reset} className="glass-pill flex items-center gap-2 hover:bg-red-500/10 hover:text-red-400 transition-colors">
            <Trash2 className="w-4 h-4" /> Resetear
          </button>
        )}
      </header>

      <main className="w-full max-w-6xl flex-1 flex flex-col gap-8">
        {!data ? (
          <div 
            className="flex-1 glass-card flex flex-col items-center justify-center p-12 border-dashed border-2 border-indigo-500/30 hover:border-indigo-500/60 transition-all group animate-fade-in"
            onDragOver={onDragOver}
            onDrop={onDrop}
          >
            <div className="p-6 bg-indigo-600/10 rounded-full mb-6 group-hover:scale-110 transition-transform">
              <Upload className="w-12 h-12 text-indigo-400" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Sube tu archivo de actividades</h2>
            <p className="text-gray-400 mb-8 text-center max-w-md">
              Arrastra y suelta tu archivo Excel (.xlsx, .xls) o HTML generado por el tacógrafo para procesar las jornadas laborales automáticamente.
            </p>
            <label className="primary px-8 py-3 rounded-xl cursor-pointer hover:opacity-90">
              Seleccionar Archivo
              <input type="file" className="hidden" onChange={handleFileUpload} accept=".xlsx,.xls,.html" />
            </label>
            {error && (
              <div className="mt-6 flex items-center gap-2 text-red-400 bg-red-400/10 px-4 py-2 rounded-lg">
                <AlertCircle className="w-4 h-4" /> {error}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-8 animate-fade-in">
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="glass-card p-6 flex items-center gap-4">
                <div className="p-3 bg-blue-500/10 rounded-xl">
                  <Calendar className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Total Jornadas</p>
                  <p className="text-2xl font-bold">{stats.totalDays}</p>
                </div>
              </div>
              <div className="glass-card p-6 flex items-center gap-4">
                <div className="p-3 bg-purple-500/10 rounded-xl">
                  <Coffee className="w-6 h-6 text-purple-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Descansos Detectados</p>
                  <p className="text-2xl font-bold">{stats.totalBreaks}</p>
                </div>
              </div>
              <div className="glass-card p-6 flex items-center gap-4">
                <div className="p-3 bg-indigo-500/10 rounded-xl">
                  <CheckCircle2 className="w-6 h-6 text-indigo-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Estado</p>
                  <p className="text-2xl font-bold text-green-400">Correcto</p>
                </div>
              </div>
            </div>

            {/* Table */}
            <div className="glass-card overflow-hidden">
              <div className="p-6 border-b border-white/5 flex justify-between items-center">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <FileSpreadsheet className="w-5 h-5 text-indigo-400" />
                  Resultados del Procesamiento
                </h3>
                <button onClick={exportToExcel} className="primary flex items-center gap-2">
                  <Download className="w-4 h-4" /> Exportar a Excel
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-white/5 text-xs uppercase tracking-wider text-gray-400 font-medium">
                      <th className="px-6 py-4">Día</th>
                      <th className="px-6 py-4">Inicio Jornada</th>
                      <th className="px-6 py-4">Fin Jornada</th>
                      <th className="px-6 py-4">Descansos</th>
                      <th className="px-6 py-4 text-center">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {data.map((row, i) => (
                      <tr key={i} className="hover:bg-white/5 transition-colors group">
                        <td className="px-6 py-4 font-medium">{row.Dia}</td>
                        <td className="px-6 py-4">
                          <span className="flex items-center gap-2">
                            <Clock className="w-3 h-3 text-green-400" /> {row['Inicio Jornada']}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="flex items-center gap-2">
                            <Clock className="w-3 h-3 text-red-400" /> {row['Fin Jornada']}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="flex items-center gap-2 text-gray-400">
                             {row['Descansos']}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <button className="p-1 hover:text-indigo-400">
                            <ChevronRight className="w-5 h-5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="w-full max-w-6xl mt-12 py-6 text-center text-gray-500 text-sm border-t border-white/5">
        &copy; {new Date().getFullYear()} Tacógrafo Pro - Desarrollado para JME
      </footer>

      {loading && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white/5 p-8 rounded-3xl border border-white/10 flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
            <p className="font-medium">Procesando actividades...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
