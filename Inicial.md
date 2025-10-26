## Roadmap operativo

El objetivo es tener una base mínima funcional que:

- Recoja eventos desde varios sitios (Crawl4AI + Playwright).
- Guarde la información cruda por fuente.
- Normalice fechas/categorías y consolide todo en un único dataset.
- Exponga los eventos en una interfaz rápida (Streamlit) lista para iterar.

---

## 1. Estructura del workspace

````
crawler-evento/
├── crawl_configs/         # YAML con schema/extractores por sitio
│   └── python_events.yaml
├── crawlers/
│   └── do_crawls.py       # CLI para ejecutar los crawls definidos
├── data/
│   ├── eventos_raw/       # Salida cruda por origen
│   └── processed/         # Datos limpios y agregados
 ├── process/
 │   └── clean_and_merge.py # Normalización y agrupaciones
 ├── frontend/
 │   └── app.py             # Streamlit (MVP)
 ├── requirements.txt
 └── README.md              # Pasos de instalación y uso
```yaml
url: https://www.python.org/events/python-events/
description: Lista oficial de la PSF
schema:
    name: python_org_events
    baseSelector: '.list-recent-events li'
    fields:
        - name: title
            selector: 'h3'
            type: text
        - name: date
            selector: 'time'
            type: text
        - name: location
            selector: '.event-location'
            type: text
        - name: description
            selector: 'p'
            type: text
        - name: link
            selector: 'h3 a'
            type: attribute
            attribute: href
postprocess:
    date_format_hint: '%d %b %Y'
    timezone: Europe/London
````

Cuando añadas un nuevo site, solo replicas este patrón cambiando selectores/hints.

---

## 3. Ejecución del crawler

`crawlers/do_crawls.py` carga todos los YAML, construye `CrawlerRunConfig` y llama a `AsyncWebCrawler`.

CLI:

```bash
python -m crawlers.do_crawls          # Ejecuta todos los YAML
python -m crawlers.do_crawls --only python_events  # Solo uno
```

Salida por archivo en `data/eventos_raw/{nombre}.json` con metadata, items y postprocess.

> Si Crawl4AI devuelve JSON string en `result.extracted_content`, la herramienta lo parsea; en caso contrario deja una lista vacía para diagnosticar.

---

## 4. Limpieza y consolidación

`process/clean_and_merge.py` recorre los JSON crudos, aplica:

- Parseo flexible de fechas (`dateutil.parser` + hints de `postprocess`).
- Normalización ligera de categorías.
- Creación de campos uniformes (`title`, `date`, `date_display`, `location`, etc.).

Genera dos archivos:

- `data/processed/eventos.json`: lista plana para consumo en APIs.
- `data/processed/eventos_por_dia.json`: diccionario `{fecha: [eventos...]}` pensado para la UI.

Ejecución:

```bash
python -m process.clean_and_merge
```

---

## 5. Interfaz rápida

`frontend/app.py` usa Streamlit para cargar `eventos_por_dia.json` y visualizar:

- Selector de fecha (prefiere hoy si existe data).
- Selector de categoría dinámico.
- Tarjetas con resumen, link al evento y referencia a la fuente.

Lanzamiento:

```bash
streamlit run frontend/app.py
```

---

## 6. Flujo recomendado

1. Crear/ajustar YAMLs en `crawl_configs/`.
2. `python -m crawlers.do_crawls` para obtener datos crudos.
3. `python -m process.clean_and_merge` para normalizar.
4. `streamlit run frontend/app.py` para visualizar.

Repite los pasos 1–3 cada vez que añadas una nueva fuente.

---

## 7. Próximas extensiones

- Añadir logging estructurado y reintentos en `do_crawls.py`.
- Guardar también el Markdown de Crawl4AI para análisis semántico.
- Validar eventos con tests unitarios (ej. categorías/date parsing).
- Reemplazar Streamlit por FastAPI + frontend a medida cuando la lógica crezca.

---

## 8. Exponer API mínima (siguiente paso)

- Construir un endpoint `GET /eventos` con FastAPI que entregue el contenido de `data/processed/eventos.json` con soporte de filtros básicos (`fecha`, `categoría`).
- Añadir script `backend/app.py` con un `uvicorn` configurable (`uvicorn backend.app:app --reload`).
- Automatizar la regeneración de datos antes de levantar la API (invocar `python -m process.clean_and_merge` si `eventos.json` está desactualizado).
- Documentar en `README.md` cómo levantar el backend y cómo consumir el endpoint desde la interfaz o herramientas externas.
