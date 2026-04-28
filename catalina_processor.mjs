import * as XLSX from 'xlsx';
import { processTacografoData } from './Proyecto Tacografo/src/utils/tacografoLogic.js';

const inputPath = process.argv[2];
const outputPath = process.argv[3];

if (!inputPath || !outputPath) {
    console.error('Usage: node catalina_processor.mjs <input_excel> <output_excel>');
    process.exit(1);
}

import fs from 'fs';

try {
    const fileBuffer = fs.readFileSync(inputPath);
    const wb = XLSX.read(fileBuffer, { type: 'buffer', cellDates: true });
    const wsname = wb.SheetNames[0];
    const ws = wb.Sheets[wsname];

    // Robustly find the header row just like App.jsx
    const fullData = XLSX.utils.sheet_to_json(ws, { header: 1 });
    const headerRowIndex = fullData.findIndex(row =>
        row.includes('Tarjeta') && row.includes('Actividad') && (row.includes('Inicio') || row.includes('Comienzo'))
    );

    if (headerRowIndex === -1) {
        throw new Error('No se pudo encontrar la fila de encabezados (Tarjeta, Actividad, Inicio).');
    }

    const rawData = XLSX.utils.sheet_to_json(ws, { range: headerRowIndex });

    // Process data using the exact same logic
    const processed = processTacografoData(rawData);

    if (processed.length === 0) {
        throw new Error('No se encontraron datos válidos en el archivo.');
    }

    // Get available months
    const availableMonths = [...new Set(processed.map(r => {
        const [d, m, y] = r.Dia.split('/');
        return `${y}-${m}`;
    }))].sort();

    const targetMonth = process.argv[4]; // Optional: YYYY-MM or 'ALL'

    if (!targetMonth) {
        // Just report available months
        console.log('AVAILABLE_MONTHS:' + JSON.stringify(availableMonths));
        process.exit(0);
    }

    // Filter by month
    const filteredData = targetMonth === 'ALL' ? processed : processed.filter(r => {
        const [d, m, y] = r.Dia.split('/');
        return `${y}-${m}` === targetMonth;
    });

    if (filteredData.length === 0) {
        throw new Error(`No hay datos para el mes ${targetMonth}`);
    }

    // Export to Excel (removing the _rawDate property used for sorting)
    const exportData = filteredData.map(({ _rawDate, ...rest }) => rest);
    const newWs = XLSX.utils.json_to_sheet(exportData);
    const newWb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(newWb, newWs, "Jornadas");
    XLSX.writeFile(newWb, outputPath);

    console.log(`Successfully processed: ${outputPath}`);
} catch (err) {
    console.error(`Error processing file ${inputPath}:`, err.message);
    process.exit(1);
}
