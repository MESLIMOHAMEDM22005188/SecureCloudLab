from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="SecureCloudLab")

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
      <head><title>SecureCloudLab</title></head>
      <body>
        <h1>SecureCloudLab</h1>
        <p>Dashboard local opérationnel.</p>
        <a href="/docs">Ouvrir la documentation de l'API</a>
      </body>
    </html>
    """