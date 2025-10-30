# Guía de recarga de eventos

> Windows PowerShell, ejecutar desde `C:\PRUEBAS\CRAWLER-EVENTO`.

## 1. Preparación del entorno

- `python -m venv .venv` – crea el entorno virtual si todavía no existe.
- `.\.venv\Scripts\Activate.ps1` – activa el entorno virtual.
- `pip install -r requirements.txt` – asegura que las dependencias estén al día.

## 2. Recarga manual completa

1. `python -m crawlers.do_crawls` – vuelve a lanzar todos los scrapers definidos en `crawl_configs/`.
2. `python -m process.clean_and_merge` – normaliza y genera `data/processed/eventos.json` y `eventos_por_dia.json`.
3. (Opcional) `streamlit run frontend/app.py` – revisa la interfaz para validar los datos.

> Tip rápido: si solo quieres refrescar sin revisar la interfaz, ejecuta el paso 1 y luego el 2.

## 3. Automatizar la recarga en local

- **Tarea programada (Windows Task Scheduler):**
  - Programa un script `.ps1` que active el entorno y ejecute los pasos 1 y 2 cada día a la hora deseada.
  - Ejemplo de script `recarga.ps1`:
    ```powershell
    cd C:\PRUEBAS\CRAWLER-EVENTO
    .\.venv\Scripts\Activate.ps1
    python -m crawlers.do_crawls
    python -m process.clean_and_merge
    ```
- **Recordatorio manual:** Configura un recordatorio diario para lanzar la recarga antes de publicar los datos.

## 4. Ejecutarlo en un servidor o servicio externo

- Necesitas un entorno capaz de ejecutar Python (por ejemplo, una VM, un contenedor o un servicio como GitHub Actions).
- Asegura que el servidor tenga acceso a los sitios de origen y que Playwright pueda instalar/usar Chromium.
- Protege credenciales o claves si se añaden en el futuro.

## 5. Publicar los datos actualizados

- Si no puedes ejecutar el crawler en el hosting del sitio final, haz la recarga en local y sube los ficheros procesados (`data/processed/*.json`).
- Automatiza el despliegue con:
  - `git push` hacia el repositorio remoto (si tu hosting toma el repositorio como origen).
  - Sincronización directa del archivo `eventos.json` con el servidor (por FTP/SFTP/rsync).

## 6. ¿Qué opción elegir?

- **Servidor con Python y Playwright disponible:** automatiza allí para que se refresque solo (cron, systemd timers, GitHub Actions + almacenamiento remoto).
- **Servidor sin permisos para ejecutar crawlers:** recarga en local y publica los ficheros finales.
- **Sin tiempo para automatizar ya:** realiza la recarga manual siguiendo la sección 2 y agenda tareas recurrentes.

Mantén un registro breve de cada recarga (fecha, incidencias) para detectar cambios inesperados en las fuentes.
