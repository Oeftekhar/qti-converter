import tempfile, subprocess, pathlib, shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

INDEX_HTML = """
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>TXT → QTI (Canvas)</title></head>
  <body style="font-family:system-ui;max-width:700px;margin:2rem auto;line-height:1.5">
    <h1>Convert formatted text → QTI .zip</h1>
    <form action="/convert" method="post" enctype="multipart/form-data">
      <p><input type="file" name="file" accept=".txt" required></p>
      <button>Convert</button>
    </form>
    <p style="color:#555">Upload a .txt file that follows the <a href="https://github.com/gpoore/text2qti" target="_blank" rel="noopener">text2qti</a> format.</p>
  </body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML

@app.post("/convert")
def convert(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Please upload a .txt file")

    workdir = pathlib.Path(tempfile.mkdtemp())
    src = workdir / file.filename
    with src.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run text2qti on the uploaded file
    result = subprocess.run(["text2qti", str(src)], cwd=workdir, capture_output=True, text=True)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"text2qti error:\n{result.stderr}")

    zip_path = src.with_suffix(".zip")
    if not zip_path.exists():
        zips = list(workdir.glob("*.zip"))
        if not zips:
            raise HTTPException(status_code=500, detail="QTI zip not found.")
        zip_path = zips[0]

    return FileResponse(path=str(zip_path), media_type="application/zip", filename=zip_path.name)
