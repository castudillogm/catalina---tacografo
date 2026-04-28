import * as XLSX from 'xlsx';

/**
 * Processes tacograph activity data mimicking the Pandas logic in the notebook.
 * @param {Array} data - Array of objects representing rows from the Excel/HTML file.
 * @returns {Array} - Processed "Jornadas" (working days).
 */
export const processTacografoData = (data) => {
  if (!data || data.length === 0) return [];

  // Helper to parse date strings "DD/MM/YYYY HH:mm"
  const parseDate = (dateVal) => {
    if (!dateVal) return null;

    // Handle Date objects directly
    if (dateVal instanceof Date) return dateVal;

    // Handle Excel serial dates
    if (typeof dateVal === 'number') {
      return new Date(Math.round((dateVal - 25569) * 86400 * 1000));
    }

    // Handle strings "DD/MM/YYYY HH:mm"
    if (typeof dateVal === 'string') {
      const [datePart, timePart] = dateVal.split(' ');
      if (!datePart || !timePart) return null;
      const [day, month, year] = datePart.split('/');
      const [hours, minutes] = timePart.split(':');
      const d = new Date(year, month - 1, day, hours || 0, minutes || 0);
      return isNaN(d.getTime()) ? null : d;
    }

    return null;
  };

  // 1. Map and Parse initial data
  const rows = data.map(row => {
    const inicio = parseDate(row.Inicio);
    const fin = parseDate(row.Fin);
    const dia = inicio ? `${String(inicio.getDate()).padStart(2, '0')}/${String(inicio.getMonth() + 1).padStart(2, '0')}/${inicio.getFullYear()}` : null;

    return {
      ...row,
      Inicio: inicio,
      Fin: fin,
      Dia: dia,
      DuracionMs: (inicio && fin) ? fin - inicio : 0,
    };
  }).filter(row => row.Inicio && row.Fin && row.Dia);

  // 2. Group by Dia
  const groups = {};
  rows.forEach(row => {
    if (!groups[row.Dia]) groups[row.Dia] = [];
    groups[row.Dia].push(row);
  });

  // 3. Process each day
  const result = Object.keys(groups).map(dia => {
    const dayRows = groups[dia];
    const nonDesRows = dayRows.filter(r => r.Actividad && r.Actividad.toUpperCase() !== 'DES');

    if (nonDesRows.length === 0) return null;

    // Inicio y fin de la jornada (primer y último registro no-DES)
    const inicioJornada = new Date(Math.min(...nonDesRows.map(r => r.Inicio.getTime())));
    const finJornada = new Date(Math.max(...nonDesRows.map(r => r.Fin.getTime())));

    // Filtrar descansos que estén dentro de la jornada
    const desRows = dayRows.filter(r => r.Actividad && r.Actividad.toUpperCase() === 'DES');
    const filteredDescansos = desRows.filter(r =>
      r.Inicio >= inicioJornada && r.Fin <= finJornada
    );

    // Sumar duración de esos descansos
    const totalDescansosMs = filteredDescansos.reduce((sum, r) => sum + r.DuracionMs, 0);

    // Cálculo de la nueva columna solicitada: Fin - Inicio - Descansos
    const jornadaTotalMs = finJornada - inicioJornada;
    const diferenciaMs = jornadaTotalMs - totalDescansosMs;

    const formatTime = (date) => `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    const formatDuration = (ms) => {
      const minutes = Math.floor(ms / (1000 * 60));
      const h = Math.floor(minutes / 60);
      const m = minutes % 60;
      return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
    };

    // Obtener la tarjeta de cualquier fila del día (asumimos que es la misma)
    const tarjeta = dayRows[0]?.Tarjeta || "UNKNOWN";

    return {
      'Tarjeta': tarjeta,
      'Dia': dia,
      'Inicio Jornada': formatTime(inicioJornada),
      'Fin Jornada': formatTime(finJornada),
      'Descansos': formatDuration(totalDescansosMs),
      'Dif JOR-DES': formatDuration(diferenciaMs),
      // Raw data for sorting
      _rawDate: new Date(dia.split('/').reverse().join('-'))
    };
  }).filter(r => r !== null);

  // 4. Sort by Dia
  return result.sort((a, b) => a._rawDate - b._rawDate);
};
