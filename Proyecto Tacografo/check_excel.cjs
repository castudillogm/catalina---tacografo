const XLSX = require('xlsx');
try {
  const wb = XLSX.readFile('C:\\Users\\jmescudero\\Desktop\\JME\\C_E18237829W000003_E_M LLADO.xls.xlsx');
  const ws = wb.Sheets[wb.SheetNames[0]];
  const data = XLSX.utils.sheet_to_json(ws, { header: 1 });
  console.log(JSON.stringify(data.slice(0, 5), null, 2));
} catch (e) {
  console.error(e.message);
}
