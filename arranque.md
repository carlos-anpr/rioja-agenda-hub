# Guía rápida de arranque

> Windows PowerShell, ejecutar desde `C:\PRUEBAS\CRAWLER-EVENTO`.

- `python -m venv .venv` – crea el entorno virtual local.
- `.\.venv\Scripts\Activate.ps1` – activa el entorno virtual.
- `python -m pip install --upgrade pip` – actualiza pip en el entorno.
- `pip install -r requirements.txt` – instala las dependencias del proyecto.
- `crawl4ai-setup` – descarga recursos base de Crawl4AI.
- `python -m playwright install --with-deps chromium` – instala el navegador para Playwright.

## Ejecutar el pipeline

- `python -m crawlers.do_crawls` – lanza todos los scrapers definidos en `crawl_configs/`.
- `python -m process.clean_and_merge` – normaliza/agrupa los datos en `data/processed/`.

## Arrancar la interfaz

- `streamlit run frontend/app.py` – levanta el front en modo desarrollo (abre el navegador por defecto).
