package main

import (
	"archive/zip"
	"fmt"
	"html/template"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

type ProcessResult struct {
	OriginalName string
	ExcelName    string
	DownloadURL  string
	Success      bool
	Error        string
	Months       []string
}

type BatchResult struct {
	ID      string
	Results []ProcessResult
	ZipURL  string
}

func main() {
	// Static files
	http.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("./web/static"))))

	// Routes
	http.HandleFunc("/", handleIndex)
	http.HandleFunc("/upload", handleUpload)
	http.HandleFunc("/download/", handleDownload)
	http.HandleFunc("/download-processed/", handleDownloadProcessed)
	http.HandleFunc("/download-decoded/", handleDownloadDecoded)
	http.HandleFunc("/download-zip/", handleDownloadZip)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	fmt.Println("Server starting on port " + port)
	log.Fatal(http.ListenAndServe(":" + port, nil))
}

func handleIndex(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, "./web/templates/index.html")
}

func handleUpload(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Redirect(w, r, "/", http.StatusSeeOther)
		return
	}

	err := r.ParseMultipartForm(500 << 20) // 500MB max
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	files := r.MultipartForm.File["tgd_files"]
	if len(files) == 0 {
		http.Error(w, "No files uploaded", http.StatusBadRequest)
		return
	}

	batchID := time.Now().Format("20060102_150405")
	batchDir := filepath.Join("web", "outputs", batchID)
	os.MkdirAll(batchDir, 0755)

	uploadDir := filepath.Join("web", "uploads", batchID)
	os.MkdirAll(uploadDir, 0755)

	batch := BatchResult{ID: batchID}

	// 1. First Pass: Save and Decode all uploaded files
	for _, fileHeader := range files {
		tgdPath := filepath.Join(uploadDir, fileHeader.Filename)
		dst, _ := os.Create(tgdPath)
		src, _ := fileHeader.Open()
		io.Copy(dst, src)
		dst.Close()
		src.Close()

		jsonPath := tgdPath + ".json"
		decoderBin := "./dddparser"
		if runtime.GOOS == "windows" {
			decoderBin = "./dddparser.exe"
		}
		
		fmt.Printf("Decoding: %s\n", fileHeader.Filename)
		cmdParse := exec.Command(decoderBin, "-card", "-input", tgdPath, "-output", jsonPath)
		if out, err := cmdParse.CombinedOutput(); err != nil {
			fmt.Printf("DECODER ERROR on %s: %v | Output: %s\n", fileHeader.Filename, err, string(out))
		}
	}

	// 2. Consolidation Step
	consolidatedDir := filepath.Join("web", "outputs", batchID, "consolidated")
	os.MkdirAll(consolidatedDir, 0755)
	fmt.Println("Consolidating JSONs...")
	cmdConsolidate := exec.Command("python", "consolidar_jsons.py", uploadDir, consolidatedDir)
	if out, err := cmdConsolidate.CombinedOutput(); err != nil {
		fmt.Printf("CONSOLIDATION ERROR: %v | Output: %s\n", err, string(out))
	} else {
		fmt.Printf("Consolidation output: %s\n", string(out))
	}

	// 3. Second Pass: Process consolidated files
	consolidatedFiles, _ := os.ReadDir(consolidatedDir)
	if len(consolidatedFiles) == 0 {
		fmt.Println("WARNING: No consolidated files found!")
	}

	for _, f := range consolidatedFiles {
		if !strings.HasSuffix(f.Name(), ".json") { continue }
		
		jsonPath := filepath.Join(consolidatedDir, f.Name())
		baseName := strings.TrimSuffix(f.Name(), ".json")
		res := ProcessResult{OriginalName: baseName}
		
		fmt.Printf("Processing Consolidated: %s\n", f.Name())

		// 1. Run Excel Generator
		rawExcelPath := filepath.Join(batchDir, baseName + "_raw.xlsx")
		cmdExcel := exec.Command("python", "json_to_excel.py", jsonPath, rawExcelPath)
		if out, err := cmdExcel.CombinedOutput(); err != nil {
			fmt.Printf("EXCEL GEN ERROR: %v | Output: %s\n", err, string(out))
			res.Error = "Excel Gen Error"
			batch.Results = append(batch.Results, res)
			continue
		}

		// 2. Run Catalina Processor
		excelName := baseName + "_TGD_Tratado.xlsx"
		excelPath := filepath.Join(batchDir, excelName)
		cmdProc := exec.Command("node", "catalina_processor.mjs", rawExcelPath, excelPath, "ALL")
		if out, err := cmdProc.CombinedOutput(); err != nil {
			fmt.Printf("CATALINA PROC ERROR: %v | Output: %s\n", err, string(out))
			res.Error = "Processor Error"
			batch.Results = append(batch.Results, res)
			continue
		}

		// 3. Dummy Pass for Months
		cmdNodeInit := exec.Command("node", "catalina_processor.mjs", rawExcelPath, "DUMMY")
		outInit, _ := cmdNodeInit.CombinedOutput()
		outStr := string(outInit)
		if strings.Contains(outStr, "AVAILABLE_MONTHS:") {
			jsonPart := strings.Split(outStr, "AVAILABLE_MONTHS:")[1]
			jsonPart = strings.TrimSpace(jsonPart)
			if idx := strings.Index(jsonPart, "\n"); idx != -1 {
				jsonPart = jsonPart[:idx]
			}
			res.Months = strings.Split(strings.Trim(jsonPart, "[]\""), "\",\"")
			var cleanMonths []string
			for _, m := range res.Months {
				if m != "" && m != "[]" {
					cleanMonths = append(cleanMonths, m)
				}
			}
			res.Months = cleanMonths
		}

		res.Success = true
		res.ExcelName = excelName 
		batch.Results = append(batch.Results, res)
	}

	// Final Step: Create Zip
	successCount := 0
	for _, r := range batch.Results {
		if r.Success { successCount++ }
	}

	if successCount > 0 {
		zipName := batchID + "_all_excels.zip"
		zipPath := filepath.Join("web", "outputs", zipName)
		zFile, _ := os.Create(zipPath)
		zWriter := zip.NewWriter(zFile)
		for _, r := range batch.Results {
			if r.Success {
				fullExcelPath := filepath.Join(batchDir, r.ExcelName)
				f, err := os.Open(fullExcelPath)
				if err != nil {
					fmt.Printf("ZIP ERROR: Could not open file %s: %v\n", fullExcelPath, err)
					continue
				}
				wZip, _ := zWriter.Create(r.ExcelName)
				io.Copy(wZip, f)
				f.Close()
			}
		}
		zWriter.Close()
		zFile.Close()
		fmt.Printf("ZIP Created Successfully: %s\n", zipPath)
	} else {
		fmt.Println("ERROR: No successful results to ZIP.")
	}

	batch.ZipURL = "/download-zip/" + batchID

	// Render Results with a simple template
	tmpl := `
	<!DOCTYPE html>
	<html lang="es">
	<head>
		<meta charset="UTF-8"><title>Resultados - Tacógrafo Catalina</title>
		<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
		<style>
			body { font-family: 'Outfit', sans-serif; background: #0f172a; color: white; padding: 2rem; display: flex; justify-content: center; }
			.card { background: #1e293b; padding: 2rem; border-radius: 20px; width: 100%; max-width: 900px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
			.header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
			.item { display: flex; justify-content: space-between; align-items: center; padding: 15px; border-bottom: 1px solid #334155; }
			.item:last-child { border-bottom: none; }
			.success { color: #10b981; }
			.error { color: #ef4444; font-size: 0.8rem; }
			.btn { background: #6366f1; color: white; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; border: none; cursor: pointer; }
			.btn:hover { background: #4f46e5; transform: translateY(-1px); }
			.btn-zip { background: #10b981; }
			.btn-zip:hover { background: #059669; }
			.tag { background: #312e81; color: #c7d2fe; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; margin-left: 10px; }
			.checkbox-group { display: flex; gap: 10px; font-size: 0.85rem; color: #94a3b8; }
			.checkbox-group label { display: flex; align-items: center; gap: 5px; cursor: pointer; }
			.checkbox-group input { cursor: pointer; accent-color: #6366f1; }
		</style>
	</head>
	<body>
		<div class="card">
			<div class="header-row">
				<h1>Tacógrafo Catalina</h1>
				<div class="bulk-actions">
					<div class="checkbox-group">
						<label><input type="checkbox" id="bulk-treated" checked> Tratados</label>
						<label><input type="checkbox" id="bulk-decoded"> Decodificados</label>
					</div>
					<select id="global-month" class="month-select">
						<option value="">Todos los meses</option>
					</select>
					<button onclick="downloadBulk()" class="btn btn-zip">Descargar Todo (ZIP)</button>
				</div>
			</div>

			<div class="list">
				{{ $bid := .ID }}
				{{ range .Results }}
					<div class="item" data-filename="{{ .OriginalName }}">
						<div>
							<strong>{{ .OriginalName }}</strong>
							{{ if not .Success }}<br><span class="error">{{ .Error }}</span>{{ end }}
						</div>
						{{ if .Success }}
							<div class="actions">
								<div class="checkbox-group">
									<label><input type="checkbox" class="row-treated" checked> Tratado</label>
									<label><input type="checkbox" class="row-decoded"> Decodificado</label>
								</div>
								<select class="month-select row-month">
									<option value="">Completo</option>
									{{ range .Months }}
										<option value="{{ . }}">{{ . }}</option>
									{{ end }}
								</select>
								<button onclick="downloadRow(this, '{{ $bid }}', '{{ .OriginalName }}')" class="btn">Descargar</button>
							</div>
						{{ end }}
					</div>
				{{ end }}
			</div>
			<br><a href="/" style="color: #94a3b8; text-decoration: none; font-size: 0.9rem;">← Volver a subir</a>
		</div>

		<script>
			function downloadRow(btn, bid, originalName) {
				const parent = btn.closest('.actions');
				const treated = parent.querySelector('.row-treated').checked;
				const decoded = parent.querySelector('.row-decoded').checked;
				const month = parent.querySelector('.row-month').value || "ALL";

				if (!treated && !decoded) {
					alert("Selecciona al menos una casilla (Tratado o Decodificado)");
					return;
				}

				if (treated && !decoded) {
					window.location.href = "/download-processed/" + bid + "/" + originalName + "?month=" + month;
				} else if (!treated && decoded) {
					window.location.href = "/download-decoded/" + bid + "/" + originalName;
				} else {
					// Both: download a small zip for this row
					window.location.href = "/download-zip/" + bid + "?files=" + originalName + "&month=" + month + "&types=both";
				}
			}

			function downloadBulk() {
				const treated = document.getElementById('bulk-treated').checked;
				const decoded = document.getElementById('bulk-decoded').checked;
				const month = document.getElementById('global-month').value;
				const bid = "{{ .ID }}";

				if (!treated && !decoded) {
					alert("Selecciona al menos una casilla (Tratados o Decodificados)");
					return;
				}

				let typeParam = "treated";
				if (treated && decoded) typeParam = "both";
				else if (decoded) typeParam = "decoded";

				let url = "/download-zip/" + bid + "?types=" + typeParam;
				if (month) url += "&month=" + month;
				window.location.href = url;
			}

			// Populate global month from all available
			const allMonths = new Set();
			document.querySelectorAll('.row-month option').forEach(opt => {
				if(opt.value) allMonths.add(opt.value);
			});
			const globalSelect = document.getElementById('global-month');
			Array.from(allMonths).sort().forEach(m => {
				const opt = document.createElement('option');
				opt.value = m;
				opt.textContent = m;
				globalSelect.appendChild(opt);
			});
		</script>
	</body>
	</html>`
	
	t := template.Must(template.New("res").Parse(tmpl))
	t.Execute(w, batch)
}

func handleDownload(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/download/")
	filePath := filepath.Join("web", "outputs", path)
	http.ServeFile(w, r, filePath)
}

func handleDownloadProcessed(w http.ResponseWriter, r *http.Request) {
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 4 { return }
	batchID := parts[2]
	originalName := parts[3]
	month := r.URL.Query().Get("month")

	// 1. Get raw excel path (the one generated by Python)
	excelName := strings.TrimSuffix(originalName, filepath.Ext(originalName)) + "_raw.xlsx"
	rawPath := filepath.Join("web", "outputs", batchID, excelName)

	// 2. Prepare final path
	suffix := "_TGD_Tratado.xlsx"
	if month != "" { suffix = "_" + month + "_TGD_Tratado.xlsx" }
	finalName := strings.TrimSuffix(originalName, filepath.Ext(originalName)) + suffix
	finalPath := filepath.Join("web", "outputs", batchID, finalName)

	// 3. Process with Node
	if (month == "") { month = "ALL" }
	args := []string{"catalina_processor.mjs", rawPath, finalPath, month}
	cmd := exec.Command("node", args...)
	if out, err := cmd.CombinedOutput(); err != nil {
		http.Error(w, fmt.Sprintf("Processing error: %v | %s", err, string(out)), 500)
		return
	}

	w.Header().Set("Content-Disposition", "attachment; filename="+finalName)
	http.ServeFile(w, r, finalPath)
}

func handleDownloadDecoded(w http.ResponseWriter, r *http.Request) {
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 4 { return }
	batchID := parts[2]
	originalName := parts[3]

	// The python script already generated the initial excel in outputs during upload
	excelName := strings.TrimSuffix(originalName, filepath.Ext(originalName)) + "_raw.xlsx"
	excelPath := filepath.Join("web", "outputs", batchID, excelName)

	w.Header().Set("Content-Disposition", "attachment; filename="+excelName)
	http.ServeFile(w, r, excelPath)
}

func handleDownloadZip(w http.ResponseWriter, r *http.Request) {
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 3 { return }
	batchID := parts[2]
	
	month := r.URL.Query().Get("month")
	types := r.URL.Query().Get("types") // treated, decoded, both
	specificFiles := r.URL.Query().Get("files")

	consolidatedDir := filepath.Join("web", "outputs", batchID, "consolidated")
	var filesToProcess []string
	if specificFiles != "" {
		// If specific files requested, we still use those IDs but map them correctly
		filesToProcess = strings.Split(specificFiles, ",")
	} else {
		// Use the consolidated files as the source of truth for "Download All"
		entries, _ := os.ReadDir(consolidatedDir)
		for _, e := range entries {
			if strings.HasSuffix(e.Name(), ".json") {
				filesToProcess = append(filesToProcess, e.Name())
			}
		}
	}

	zipName := batchID + "_Descarga"
	if month != "" && types != "decoded" { zipName += "_" + month }
	zipName += ".zip"
	zipPath := filepath.Join("web", "outputs", zipName)

	zFile, _ := os.Create(zipPath)
	zWriter := zip.NewWriter(zFile)

	for _, originalName := range filesToProcess {
		// 1. Decoded (Excel bruto format Camila)
		if types == "decoded" || types == "both" {
			excelName := strings.TrimSuffix(originalName, filepath.Ext(originalName)) + "_raw.xlsx"
			rawExcelPath := filepath.Join("web", "outputs", batchID, excelName)
			f, err := os.Open(rawExcelPath)
			if err == nil {
				wZip, _ := zWriter.Create(excelName)
				io.Copy(wZip, f)
				f.Close()
			}
		}

		// 2. Treated (Excel)
		if types == "treated" || types == "both" || types == "" {
			rawExcelName := strings.TrimSuffix(originalName, filepath.Ext(originalName)) + "_raw.xlsx"
			rawExcelPath := filepath.Join("web", "outputs", batchID, rawExcelName)

			suffix := "_TGD_Tratado.xlsx"
			targetMonth := month
			if targetMonth == "" { targetMonth = "ALL" }
			if targetMonth != "ALL" { suffix = "_" + targetMonth + "_TGD_Tratado.xlsx" }
			
			finalName := strings.TrimSuffix(originalName, filepath.Ext(originalName)) + suffix
			finalPath := filepath.Join("web", "outputs", batchID, finalName)

			args := []string{"catalina_processor.mjs", rawExcelPath, finalPath, targetMonth}
			exec.Command("node", args...).Run()

			f, err := os.Open(finalPath)
			if err == nil {
				wZip, _ := zWriter.Create(finalName)
				io.Copy(wZip, f)
				f.Close()
			}
		}
	}
	zWriter.Close()
	zFile.Close()

	w.Header().Set("Content-Disposition", "attachment; filename="+zipName)
	http.ServeFile(w, r, zipPath)
}
