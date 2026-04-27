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

	fmt.Println("Server starting on http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
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

	for _, fileHeader := range files {
		res := ProcessResult{OriginalName: fileHeader.Filename}
		
		// 1. Save TGD
		tgdPath := filepath.Join(uploadDir, fileHeader.Filename)
		dst, err := os.Create(tgdPath)
		if err != nil {
			res.Error = fmt.Sprintf("Failed to create file: %v", err)
			batch.Results = append(batch.Results, res)
			continue
		}
		src, _ := fileHeader.Open()
		io.Copy(dst, src)
		dst.Close()
		src.Close()

		// 2. Run Decoder
		jsonPath := tgdPath + ".json"
		
		decoderBin := "./dddparser"
		if runtime.GOOS == "windows" {
			decoderBin = "./dddparser.exe"
		}

		cmdParse := exec.Command(decoderBin, "-card", "-input", tgdPath, "-output", jsonPath)
		if out, err := cmdParse.CombinedOutput(); err != nil {
			res.Error = fmt.Sprintf("Decoder Error: %v | Output: %s", err, string(out))
			batch.Results = append(batch.Results, res)
			continue
		}

		// 3. Run Excel Generator
		excelName := strings.TrimSuffix(fileHeader.Filename, filepath.Ext(fileHeader.Filename)) + ".xlsx"
		excelPath := filepath.Join(batchDir, excelName)
		
		// Use absolute path for safety or ensure cwd is root
		cmdExcel := exec.Command("python", "Ficheros TGD de pruebas/json_to_excel.py", jsonPath, excelPath)
		if out, err := cmdExcel.CombinedOutput(); err != nil {
			res.Error = fmt.Sprintf("Excel Gen Error: %v | Output: %s", err, string(out))
			batch.Results = append(batch.Results, res)
			continue
		}

		// 4. Run Catalina Processor (React Logic)
		finalExcelName := strings.TrimSuffix(fileHeader.Filename, filepath.Ext(fileHeader.Filename)) + "_TGD_Tratado.xlsx"
		finalExcelPath := filepath.Join(batchDir, finalExcelName)

		cmdNode := exec.Command("node", "catalina_processor.mjs", excelPath, finalExcelPath)
		if out, err := cmdNode.CombinedOutput(); err != nil {
			res.Error = fmt.Sprintf("Catalina Processor Error: %v | Output: %s", err, string(out))
			batch.Results = append(batch.Results, res)
			continue
		}

		res.Success = true
		res.ExcelName = finalExcelName
		res.DownloadURL = fmt.Sprintf("/download/%s/%s", batchID, finalExcelName)
		batch.Results = append(batch.Results, res)
	}

	// Create Zip if any success
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
				f, _ := os.Open(filepath.Join(batchDir, r.ExcelName))
				wZip, _ := zWriter.Create(r.ExcelName)
				io.Copy(wZip, f)
				f.Close()
			}
		}
		zWriter.Close()
		zFile.Close()
		batch.ZipURL = "/download/" + zipName
	}

	// Render Results with a simple template
	tmpl := `
	<!DOCTYPE html>
	<html lang="es">
	<head>
		<meta charset="UTF-8"><title>Resultados - Tacógrafo Catalina</title>
		<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
		<style>
			body { font-family: 'Outfit', sans-serif; background: #0f172a; color: white; padding: 2rem; display: flex; justify-content: center; }
			.card { background: #1e293b; padding: 2rem; border-radius: 20px; width: 100%; max-width: 800px; }
			.item { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #334155; }
			.success { color: #10b981; }
			.error { color: #ef4444; font-size: 0.8rem; }
			.btn { background: #6366f1; color: white; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-weight: 600; margin-top: 10px; display: inline-block; }
			.btn-zip { background: #10b981; margin-bottom: 20px; }
		</style>
	</head>
	<body>
		<div class="card">
			<h1>Procesamiento Finalizado - Tacógrafo Catalina</h1>
			{{ if .ZipURL }}
				<a href="{{ .ZipURL }}" class="btn btn-zip">Descargar Todo (ZIP)</a>
			{{ end }}
			<div class="list">
				{{ range .Results }}
					<div class="item">
						<div>
							<strong>{{ .OriginalName }}</strong>
							{{ if not .Success }}<br><span class="error">{{ .Error }}</span>{{ end }}
						</div>
						{{ if .Success }}
							<a href="{{ .DownloadURL }}" class="btn">Descargar Excel</a>
						{{ end }}
					</div>
				{{ end }}
			</div>
			<br><a href="/" style="color: #94a3b8;">Subir más archivos</a>
		</div>
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
