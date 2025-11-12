from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
import shutil
import os
import tempfile
from text2qti import cli as text2qti
import zipfile

app = FastAPI()

INDEX_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Collin College QTI Converter</title>
    <style>
      body {
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
        background-color: #f8fafc;
        color: #1e293b;
        margin: 0;
        padding: 0;
      }
      .container {
        max-width: 800px;
        margin: 3rem auto;
        background: #ffffff;
        padding: 2rem 2.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
      }
      h1 {
        color: #003366;
        text-align: center;
        margin-bottom: 1rem;
      }
      h2 {
        color: #003366;
        border-bottom: 2px solid #cfe1ff;
        padding-bottom: .3rem;
        margin-top: 2rem;
      }
      pre {
        background: #f1f5f9;
        padding: .5rem .75rem;
        border-radius: 8px;
        font-size: .95rem;
        line-height: 1.5;
      }
      .upload-box {
        text-align: center;
        margin: 2rem 0 1rem;
      }
      input[type=file] {
        padding: .5rem;
        border: 1px solid #ccc;
        border-radius: 8px;
        font-size: 1rem;
      }
      button {
        background: #003366;
        color: #fff;
        font-size: 1rem;
        padding: .6rem 1.25rem;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: background 0.2s ease;
      }
      button:hover {
        background: #00509e;
      }
      .logo {
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
      }
      .logo img {
        width: 220px;
        height: auto;
      }
      .message {
        text-align:center;
        margin:1rem 0;
        font-weight:600;
      }
      .error {
        color: #b91c1c;
        background:#fee2e2;
        border:1px solid #fca5a5;
        padding:.75rem;
        border-radius:8px;
        display:inline-block;
      }
      .success {
        color: #166534;
        background:#dcfce7;
        border:1px solid #86efac;
        padding:.75rem;
        border-radius:8px;
        display:inline-block;
      }
      footer {
        text-align: center;
        color: #666;
        font-size: 0.85rem;
        margin-top: 2rem;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="logo">
        <img src="https://upload.wikimedia.org/wikipedia/en/f/f2/Collin_College_logo.png" alt="Collin College Logo">
      </div>

      <h1>Collin College QTI Converter</h1>
      <p style="text-align:center;">Upload a formatted <strong>.txt</strong> quiz file and download a ready-to-import <strong>QTI .zip</strong> for Canvas.</p>

      <div class="upload-box">
        <form action="/convert" method="post" enctype="multipart/form-data">
          <input type="file" name="file" accept=".txt" required>
          <br><br>
          <button type="submit">Convert</button>
        </form>
      </div>

      {message_section}

      <h2>Formatting Instructions</h2>
      <p>Follow this structure in your text file for each question type:</p>

      <h3>1. Multiple Choice</h3>
      <pre>1. What is 2+3?
a) 6
b) 1
*c) 5</pre>

      <h3>2. True / False</h3>
      <pre>2. 2+3 is 5.
*a) True
b) False</pre>

      <h3>3. Multiple Answer</h3>
      <pre>3. Which of the following are dinosaurs?
[ ] Woolly mammoth
[*] Tyrannosaurus rex
[*] Triceratops
[ ] Smilodon fatalis</pre>

      <h3>4. Essay / Short Answer</h3>
      <pre>4. Write an essay.
___</pre>

      <h2>Tips</h2>
      <ul>
        <li>Each question must begin with a number and a period (e.g., <code>1.</code>).</li>
        <li>Use an asterisk (<code>*</code>) to mark the correct answer.</li>
        <li>Leave a blank line between questions for best results.</li>
        <li>Save your file as plain text (.txt) before uploading.</li>
      </ul>

      <footer>© Collin College • QTI Converter Resource</footer>
    </div>
  </body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return INDEX_HTML.format(message_section="")

@app.post("/convert", response_class=HTMLResponse)
async def convert(file: UploadFile):
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, file.filename)
            with open(temp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # Run text2qti conversion
            os.chdir(tmpdir)
            text2qti.main([temp_path])

            # Find the QTI zip
            for fname in os.listdir(tmpdir):
                if fname.endswith(".zip"):
                    return FileResponse(
                        os.path.join(tmpdir, fname),
                        media_type="application/zip",
                        filename=fname
                    )

            raise Exception("QTI file not found.")

    except Exception:
        message_html = """
        <div class="message">
          <div class="error">
            ⚠️ Formatting issue detected — please check your .txt file structure and try again.
          </div>
        </div>
        """
        return HTMLResponse(INDEX_HTML.format(message_section=message_html))
