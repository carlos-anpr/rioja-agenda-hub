# Crawler Evento

Pipeline inicial para recolectar eventos desde múltiples sitios con [Crawl4AI](https://github.com/unclecode/crawl4ai), dejar los datos normalizados y servirlos en una pequeña interfaz con Streamlit.

## Estructura

```
crawl_configs/        # Configuraciones YAML por sitio (selectores / prompts)
crawlers/             # Scripts asincrónicos basados en Crawl4AI
data/eventos_raw/    # Salida cruda por origen
data/processed/      # Datos ya limpios y consolidados
process/              # Limpieza y normalización
frontend/             # UI rápida (Streamlit)
requirements.txt      # Dependencias del proyecto
```

## Requisitos previos

- Python 3.10 o superior (Crawl4AI >= 0.7 requiere >= 3.10).
- Google Chrome o Chromium disponible para Playwright (Crawl4AI lo usa internamente).

## Preparar el entorno (Windows PowerShell)

```powershell
cd C:\PRUEBAS\CRAWLER-EVENTO
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Configuración inicial de Crawl4AI / Playwright
crawl4ai-setup
python -m playwright install --with-deps chromium
```

> Si la última línea falla por falta de privilegios, vuelve a ejecutarla con PowerShell como Administrador.

## Ejecutar un crawl de ejemplo

1. Ajusta o añade un YAML dentro de `crawl_configs/` si quieres cambiar selectores.
2. Lanza el crawler para una o varias fuentes (usa el nombre del archivo sin `.yaml`):

```powershell
python -m crawlers.do_crawls --only agenda_larioja
python -m crawlers.do_crawls --only elbalcon_mateo
```

El JSON resultante quedará en `data/eventos_raw/<nombre>.json`.

### Fuentes incluidas

- `agenda_larioja`: Agenda oficial de La Rioja.
- `larioja_lalistilla`: Agenda semanal de La Listilla.
- `logrono_agenda`: Agenda municipal de Logroño (con paginación).
- `planeta_rioja_planes`: Planes +55 de El Balcón Silver (con paginación).
- `elbalcon_mateo`: Agenda familiar de El Balcón de Mateo.

`elbalcon_mateo` usa generación dinámica de URLs por rango de fechas mediante `date_range` en su YAML. Puedes ajustar `days_ahead` y `chunk_days` para cubrir más/menos tiempo.

## Normalizar y consolidar datos

```powershell
python -m process.clean_and_merge
```

Esto genera `data/processed/eventos_por_dia.json` con los eventos agrupados por fecha.

## Interfaz rápida

```powershell
streamlit run frontend/app.py
```

La app carga los datos consolidados, permite filtrar por fecha y categoría, y sirve como punto de partida para extender la visualización.

## Próximos pasos sugeridos

- Añadir más configuraciones dentro de `crawl_configs/` y volver a lanzar `python -m crawlers.do_crawls`.
- Incluir lógica de _retry_ y logging estructurado en `crawlers/do_crawls.py`.
- Añadir tests para la normalización de fechas/categorías en `process/clean_and_merge.py`.
